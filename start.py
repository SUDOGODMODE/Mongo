#!/usr/bin/env python3
"""Start MongoDB, the LLM, the upload API and the incident worker in order.

Run with ``python start.py`` from any directory on macOS, Windows or Linux.
Python 3.12+ and an installed project .venv are required. Docker or Podman
provides MongoDB; llama-server is needed when the KI endpoint is not running.
Only processes started by this script are stopped when it exits. Ctrl+C stops
the API, worker and (if started here) llama-server; MongoDB remains running.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MONGO_NAME = "mongodb"
POLL_SECONDS = 1.0


class StartupError(Exception):
    """A required service could not be started or did not become ready."""


def say(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def wait_for(
    label: str,
    ready,
    timeout: float,
    process: subprocess.Popen | None = None,
) -> None:
    """Poll readiness, stopping at a deadline or when the owned child exits."""
    deadline = time.monotonic() + timeout
    while True:
        if process is not None:
            code = process.poll()
            if code is not None:
                raise StartupError(f"{label} wurde vor der Bereitschaft beendet (Code {code}).")
        if ready():
            say(f"{label} ist bereit.")
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise StartupError(f"{label} ist nach {timeout:g} s nicht bereit (Zeitlimit).")
        time.sleep(min(POLL_SECONDS, remaining))


def command(args: list[str], timeout: float = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise StartupError(f"Befehl konnte nicht ausgeführt werden: {args[0]} ({error})") from error


def python_in_venv() -> str:
    if sys.version_info < (3, 12):
        raise StartupError("Python 3.12 oder neuer ist erforderlich.")
    windows_python = ROOT / ".venv" / "Scripts" / "python.exe"
    unix_python = ROOT / ".venv" / "bin" / "python"
    candidates = [windows_python, unix_python] if os.name == "nt" else [unix_python, windows_python]
    for candidate in candidates:
        if candidate.is_file():
            result = command([str(candidate), "-c", "import sys; assert sys.version_info >= (3, 12)"])
            if result.returncode != 0:
                raise StartupError("Die Python-Version in .venv ist älter als 3.12 oder nicht lauffähig.")
            return str(candidate)
    raise StartupError(".venv fehlt. Erstelle die virtuelle Umgebung und installiere requirements.txt wie in README.md beschrieben.")


def check_dependencies(python: str) -> None:
    result = command([python, "-c", "import fastapi, uvicorn, pymongo, jsonschema, lxml, requests"])
    if result.returncode != 0:
        raise StartupError(
            f"Python-Abhängigkeiten fehlen in .venv. Installiere sie mit: "
            f'"{python}" -m pip install -r "{ROOT / "requirements.txt"}"'
        )


def container_command(runtime: str, *args: str, timeout: float = 30) -> subprocess.CompletedProcess:
    return command([runtime, *args], timeout=timeout)


def container_exists(runtime: str) -> bool:
    listed = container_command(runtime, "container", "ls", "--all", "--format", "{{.Names}}")
    if listed.returncode != 0:
        raise StartupError(f"Containerliste von {runtime} konnte nicht gelesen werden: {listed.stderr.strip()}")
    return MONGO_NAME in listed.stdout.splitlines()


def runtime_ready(runtime: str) -> bool:
    try:
        return container_command(runtime, "info", timeout=10).returncode == 0
    except StartupError:
        return False


def start_runtime(runtime: str, timeout: float) -> None:
    if runtime_ready(runtime):
        return
    deadline = time.monotonic() + timeout
    if runtime == "docker":
        launch = ("desktop", "start")
        hint = "Starte Docker Desktop bzw. die Docker Engine."
    elif sys.platform == "darwin" or os.name == "nt":
        launch = ("machine", "start")
        hint = "Initialisiere bei Bedarf einmalig mit 'podman machine init'."
    else:
        raise StartupError("Podman ist nicht erreichbar. Starte den Podman-Dienst bzw. die Maschine.")
    say(f"Starte {runtime}-Umgebung.")
    try:
        result = container_command(runtime, *launch, timeout=timeout)
    except StartupError as error:
        if runtime_ready(runtime):
            return
        raise StartupError(f"{runtime} konnte nicht gestartet werden. {hint} ({error})") from error
    if result.returncode != 0 and not runtime_ready(runtime):
        raise StartupError(f"{runtime} konnte nicht gestartet werden. {hint} {result.stderr.strip()}")
    remaining = max(0, deadline - time.monotonic())
    wait_for(f"{runtime}-Umgebung", lambda: runtime_ready(runtime), remaining)


def select_runtime(preference: str | None, timeout: float) -> str:
    available = [name for name in ("docker", "podman") if shutil.which(name)]
    if not available:
        raise StartupError("Weder Docker noch Podman ist installiert.")
    if preference is None:
        if not sys.stdin.isatty():
            raise StartupError("Ohne interaktives Terminal ist --runtime docker oder --runtime podman erforderlich.")
        say("Wähle das Container-System für MongoDB. Docker und Podman haben getrennte Daten-Volumes.")
        for number, name in enumerate(available, 1):
            print(f"  {number}) {name}", flush=True)
        choices = {name: name for name in available}
        choices.update({str(number): name for number, name in enumerate(available, 1)})
        while True:
            try:
                answer = input("Auswahl (Name oder Nummer): ").strip().lower()
            except EOFError as error:
                raise StartupError("Keine Auswahl erhalten. Verwende --runtime docker oder --runtime podman.") from error
            if answer in choices:
                preference = choices[answer]
                break
            print("Bitte einen angezeigten Namen oder eine Nummer eingeben.", flush=True)
    if preference not in available:
        raise StartupError(f"{preference} CLI fehlt. Installiere {preference} oder wähle das installierte System.")
    start_runtime(preference, timeout)
    say(f"Verwende {preference} für MongoDB.")
    return preference


def mongo_ready(python: str, url: str) -> bool:
    code = (
        "import sys; from pymongo import MongoClient; "
        "MongoClient(sys.argv[1], serverSelectionTimeoutMS=1000).admin.command('ping')"
    )
    result = command([python, "-c", code, url], timeout=5)
    return result.returncode == 0


def ensure_mongo(
    python: str, url: str, runtime_preference: str | None, runtime_timeout: float, timeout: float
) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "mongodb" or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        if mongo_ready(python, url):
            say("Externer MongoDB-Server ist bereit.")
            return
        raise StartupError("Konfigurierter MongoDB-Server ist nicht erreichbar. Prüfe MONGO_URL.")
    try:
        port = parsed.port or 27017
    except ValueError as error:
        raise StartupError("Ungültiger Port in MONGO_URL.") from error
    runtime = select_runtime(runtime_preference, runtime_timeout)
    if not container_exists(runtime):
        if port_in_use(port):
            raise StartupError(
                f"MongoDB-Port {port} ist belegt, aber im gewählten {runtime} gibt es keinen Container '{MONGO_NAME}'. "
                "Wähle das System mit den vorhandenen Daten oder gib den Port frei."
            )
        say(f"Erstelle MongoDB-Container mit {runtime} und persistentem Volume mongodb_data.")
        result = container_command(
            runtime, "run", "-d", "--name", MONGO_NAME,
            "-p", f"127.0.0.1:{port}:27017", "-v", "mongodb_data:/data/db",
            "mongodb/mongodb-community-server:latest", timeout=max(600, timeout),
        )
        if result.returncode != 0:
            raise StartupError(f"MongoDB-Container konnte nicht angelegt werden: {result.stderr.strip()}")
    else:
        state = container_command(runtime, "inspect", "--format", "{{.State.Running}}", MONGO_NAME)
        if state.returncode != 0:
            raise StartupError(f"MongoDB-Container konnte nicht geprüft werden: {state.stderr.strip()}")
        if state.stdout.strip().lower() != "true":
            if port_in_use(port):
                raise StartupError(f"MongoDB-Port {port} ist belegt; der gewählte {runtime}-Container ist gestoppt.")
            say(f"Starte MongoDB-Container mit {runtime}.")
            result = container_command(runtime, "start", MONGO_NAME)
            if result.returncode != 0:
                raise StartupError(f"MongoDB-Container konnte nicht starten: {result.stderr.strip()}")
    wait_for("MongoDB", lambda: mongo_ready(python, url), timeout)


def llm_ready(url: str, model: str) -> bool:
    """A one-token completion verifies the exact API this project uses."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply OK"}],
        "max_tokens": 1,
        "stream": False,
    }).encode("utf-8")
    request = Request(
        url.rstrip("/") + "/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = json.load(response)
            return bool(body.get("choices"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError):
        return False


def local_llm_port(url: str) -> int | None:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise StartupError(f"LLM_URL ist keine gültige HTTP-Adresse: {url}")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as error:
        raise StartupError(f"Ungültiger Port in LLM_URL: {url}") from error
    if parsed.hostname in ("localhost", "127.0.0.1", "::1") and parsed.scheme == "http":
        return port
    return None


def spawn(args: list[str], label: str) -> subprocess.Popen:
    try:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        process = subprocess.Popen(args, cwd=ROOT, creationflags=flags)
    except OSError as error:
        raise StartupError(f"{label} konnte nicht gestartet werden: {error}") from error
    say(f"{label} gestartet (PID {process.pid}).")
    return process


def ensure_llm(url: str, model: str, timeout: float, owned: list[tuple[str, subprocess.Popen]]) -> None:
    if llm_ready(url, model):
        say("KI-Server ist bereit.")
        return
    port = local_llm_port(url)
    if port is None:
        raise StartupError(f"Externer KI-Endpunkt ist nicht bereit: {url}")
    executable = shutil.which("llama-server")
    if not executable:
        raise StartupError("KI-Endpunkt ist nicht erreichbar und 'llama-server' fehlt im PATH.")
    if port_in_use(port):
        raise StartupError(f"KI-Port {port} ist belegt, aber der KI-Endpunkt antwortet nicht korrekt.")
    say("Starte KI-Server; der erste Modelldownload kann länger dauern.")
    process = spawn([
        executable,
        "-hf", "ggml-org/gemma-3-4b-it-GGUF:Q8_0",
        "--alias", model,
        "-ngl", "all",
        "-c", "8192",
        "--port", str(port),
    ], "KI-Server")
    owned.append(("KI-Server", process))
    wait_for("KI-Server", lambda: llm_ready(url, model), timeout, process)


def api_ready(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/openapi.json", timeout=2) as response:
            return "/upload" in json.load(response).get("paths", {})
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError):
        return False


def port_in_use(port: int) -> bool:
    with socket.socket() as connection:
        connection.settimeout(1)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def ensure_api(python: str, port: int, timeout: float, owned: list[tuple[str, subprocess.Popen]]) -> None:
    if api_ready(port):
        say("Upload-API ist bereits bereit.")
        return
    if port_in_use(port):
        raise StartupError(f"API-Port {port} wird bereits von einem anderen Dienst verwendet.")
    process = spawn([python, "api.py"], "Upload-API")
    owned.append(("Upload-API", process))
    wait_for("Upload-API", lambda: api_ready(port), timeout, process)


def start_worker(python: str, owned: list[tuple[str, subprocess.Popen]]) -> None:
    process = spawn([python, "main.py"], "Importprozess")
    owned.append(("Importprozess", process))
    # main.py has no health endpoint; it waits two seconds before its first loop.
    time.sleep(3)
    code = process.poll()
    if code is not None:
        raise StartupError(f"Importprozess wurde beim Start beendet (Code {code}).")
    say("Importprozess läuft; erster Verarbeitungsdurchlauf wurde gestartet.")


def stop_owned(owned: list[tuple[str, subprocess.Popen]]) -> None:
    for label, process in reversed(owned):
        if process.poll() is None:
            say(f"Stoppe {label}.")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def positive_seconds(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("eine positive Zahl in Sekunden erwartet") from error
    if not (0 < seconds < float("inf")):
        raise argparse.ArgumentTypeError("eine positive Zahl in Sekunden erwartet")
    return seconds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("docker", "podman"), help="Container-System ohne interaktive Nachfrage auswählen")
    parser.add_argument("--runtime-timeout", "--docker-timeout", dest="runtime_timeout", type=positive_seconds, default=120)
    parser.add_argument("--mongo-timeout", type=positive_seconds, default=120)
    parser.add_argument("--llm-timeout", type=positive_seconds, default=1800)
    parser.add_argument("--api-timeout", type=positive_seconds, default=30)
    args = parser.parse_args()
    owned: list[tuple[str, subprocess.Popen]] = []
    started = time.monotonic()
    try:
        import config

        python = python_in_venv()
        check_dependencies(python)
        ensure_mongo(python, config.MONGO_URL, args.runtime, args.runtime_timeout, args.mongo_timeout)
        ensure_llm(config.LLM_URL, config.LLM_MODEL, args.llm_timeout, owned)
        ensure_api(python, config.API_PORT, args.api_timeout, owned)
        start_worker(python, owned)
        say(f"Produkt bereit nach {time.monotonic() - started:.1f} s. API: http://127.0.0.1:{config.API_PORT}/docs")
        say("Ctrl+C beendet die von diesem Skript gestarteten Prozesse.")
        while True:
            for label, process in owned:
                code = process.poll()
                if code is not None:
                    raise StartupError(f"{label} wurde unerwartet beendet (Code {code}).")
            time.sleep(1)
    except KeyboardInterrupt:
        say("Startskript wird beendet.")
        return 0
    except StartupError as error:
        say(f"Start fehlgeschlagen: {error}")
        return 1
    finally:
        stop_owned(owned)


if __name__ == "__main__":
    sys.exit(main())
