"""Minimal JSON/XML upload entry point. Run with: uvicorn api:app."""

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from config import PATH_IMPORT, API_PORT

app = FastAPI()
UPLOAD_DIR = Path(PATH_IMPORT)


@app.post("/upload")
async def upload(request: Request):
    """Save the raw request body and return its generated filename."""
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    extensions = {
        "application/json": ".json",
        "application/xml": ".xml",
        "text/xml": ".xml",
    }
    if content_type not in extensions:
        raise HTTPException(status_code=415, detail="Only JSON and XML supported")

    body = await request.body()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extensions[content_type]}"
    final_path = UPLOAD_DIR / filename
    partial_path = UPLOAD_DIR / f"{filename}.part"
    try:
        partial_path.write_bytes(body)
        # Publish the closed file in one rename; loaders ignore .part files.
        partial_path.rename(final_path)
    finally:
        partial_path.unlink(missing_ok=True)
    return {"filename": filename}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=API_PORT)
