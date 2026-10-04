"""Pure in-memory conversion. Runs inside a worker process; never touches disk."""
import io
import os

from markitdown import (
    FileConversionException,
    MarkItDown,
    StreamInfo,
    UnsupportedFormatException,
)

_md: MarkItDown | None = None


def convert_bytes(data: bytes, filename: str) -> dict:
    global _md
    if _md is None:
        # Plugins off, no LLM / Azure clients: nothing leaves the container.
        _md = MarkItDown(enable_plugins=False)
    ext = os.path.splitext(filename)[1].lower() or None
    try:
        result = _md.convert_stream(
            io.BytesIO(data), stream_info=StreamInfo(extension=ext, filename=filename)
        )
    except UnsupportedFormatException:
        # MarkItDown exceptions don't pickle across processes; return a status instead.
        return {"error": 415}
    except FileConversionException:
        return {"error": 422}
    return {"markdown": result.markdown, "title": result.title}
