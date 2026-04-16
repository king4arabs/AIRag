"""Server entry point – starts the uvicorn server programmatically."""

import uvicorn

from src.config import config


def main() -> None:
    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )


if __name__ == "__main__":
    main()
