from __future__ import annotations

import uvicorn

from web.config import load_config


def main() -> None:
    cfg = load_config()

    ssl_certfile = None
    ssl_keyfile = None
    if cfg.enable_https_lan and cfg.ssl_certfile and cfg.ssl_keyfile:
        ssl_certfile = str(cfg.ssl_certfile)
        ssl_keyfile = str(cfg.ssl_keyfile)

    uvicorn.run(
        "web.app:app",
        host=cfg.host,
        port=cfg.port,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        reload=False,
    )


if __name__ == "__main__":
    main()

