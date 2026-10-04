import asyncio
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .convert import convert_bytes

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
CONVERT_TIMEOUT_S = float(os.getenv("CONVERT_TIMEOUT_S", "60"))
WORKERS = int(os.getenv("CONVERT_WORKERS", "2"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).parent.parent / "static"))

# Log method/route/status/duration only. Never filenames or content.
log = logging.getLogger("markitdown-web")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = FastAPI(title="MarkItDown Web", docs_url=None, redoc_url=None, openapi_url=None)
_pool = ProcessPoolExecutor(max_workers=WORKERS)


def _reset_pool() -> None:
    """Kill hung workers (a timed-out future can't be cancelled) and start fresh."""
    global _pool
    old, _pool = _pool, ProcessPoolExecutor(max_workers=WORKERS)
    for p in list(getattr(old, "_processes", {}).values()):
        p.kill()
    old.shutdown(wait=False, cancel_futures=True)


@app.middleware("http")
async def headers_and_logging(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    log.info("%s %s %s %.0fms", request.method, request.url.path,
             response.status_code, (time.monotonic() - start) * 1000)
    return response


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    # Stream into memory with a hard cap; Content-Length can't be trusted.
    buf = bytearray()
    while chunk := await file.read(1024 * 1024):
        buf += chunk
        if len(buf) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // 1024 // 1024} MB limit")
    if not buf:
        raise HTTPException(422, "Empty file")

    name = os.path.basename(file.filename or "upload")
    start = time.monotonic()
    loop = asyncio.get_running_loop()
    try:
        out = await asyncio.wait_for(
            loop.run_in_executor(_pool, convert_bytes, bytes(buf), name),
            timeout=CONVERT_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        _reset_pool()
        raise HTTPException(504, "Conversion timed out")
    except Exception:  # includes BrokenProcessPool; never leak internals
        _reset_pool()
        raise HTTPException(500, "Conversion failed")
    if "error" in out:
        raise HTTPException(
            out["error"],
            "Unsupported file type" if out["error"] == 415 else "Could not convert this file",
        )
    return {
        "markdown": out["markdown"],
        "title": out["title"],
        "filename": name,
        "elapsed_ms": round((time.monotonic() - start) * 1000),
    }


@app.exception_handler(HTTPException)
async def http_exc(_: Request, exc: HTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
