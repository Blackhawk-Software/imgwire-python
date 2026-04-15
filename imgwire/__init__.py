try:
    from .client import ImgwireClient
except ModuleNotFoundError as exc:
    if exc.name in {
        "anyio",
        "dateutil",
        "httpx",
        "pydantic",
        "typing_extensions",
        "urllib3",
    }:
        raise ModuleNotFoundError(
            "imgwire runtime dependencies are not installed in this Python environment. "
            "Install the package with `pip install imgwire`, or for a local checkout run "
            "`make install-py` and use `.venv/bin/python`."
        ) from exc
    raise
from .images import ImgwireImage

__all__ = ["ImgwireClient", "ImgwireImage"]
