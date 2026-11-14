"""Upload one JSON and one XML sample. Start api.py before running this script."""

from pathlib import Path

import requests

import config


def main():
    url = f"http://{config.API_CLIENT_HOST}:{config.API_PORT}/upload"
    samples = Path(__file__).resolve().parent / config.PATH_SAMPLES

    for filename, content_type in config.UPLOAD_SAMPLES:
        # The endpoint expects the raw file body, not multipart form data.
        with (samples / filename).open("rb") as source:
            response = requests.post(
                url,
                data=source,
                headers={"Content-Type": content_type},
                timeout=config.UPLOAD_REQUEST_TIMEOUT,
            )
        response.raise_for_status()
        print(f"{filename} -> {response.json()['filename']}")


if __name__ == "__main__":
    main()
