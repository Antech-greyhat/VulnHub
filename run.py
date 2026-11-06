"""Start the Mfano portal. Defaults to loopback; Docker sets MFANO_BIND itself."""
import os

from portal import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("MFANO_BIND", "127.0.0.1"),
        port=int(os.environ.get("MFANO_PORT", "8080")),
        threaded=True,
    )
