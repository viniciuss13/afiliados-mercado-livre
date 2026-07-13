"""Runner Uvicorn para a aplicacao FastAPI de webhooks."""

import os

import uvicorn


def main() -> None:
    """Inicia o servidor FastAPI de webhooks."""
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    uvicorn.run(
        "automation_whats.webhooks.app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
