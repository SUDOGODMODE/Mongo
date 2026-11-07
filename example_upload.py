"""Upload one JSON and one XML sample. Start api.py before running this script."""

from pathlib import Path

import requests

from config import API_PORT


def main():
    url = f"http://127.0.0.1:{API_PORT}/upload"
    samples = Path(__file__).resolve().parent / "samples"

    for filename, content_type in (
        ("incidents_sample_batch_01.json", "application/json"),
        ("incidents_sample_batch_01.xml", "application/xml"),
    ):
        # The endpoint expects the raw file body, not multipart form data.
        with (samples / filename).open("rb") as source:
            response = requests.post(
                url,
                data=source,
                headers={"Content-Type": content_type},
                timeout=30,
            )
        response.raise_for_status()
        print(f"{filename} -> {response.json()['filename']}")


if __name__ == "__main__":
    main()
