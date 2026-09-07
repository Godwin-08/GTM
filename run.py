import os
import socket
from app import create_app

# Crée l'application via la factory définie dans app/__init__.py
app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")

    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    print("\n" + "=" * 60)
    print("  GALAXY TRAINING MANAGER (GTM) — Galaxy Solutions")
    print(f"  * Accès local       : http://localhost:{port}")
    print(f"  * Accès réseau/Wi-Fi: http://{local_ip}:{port}")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug)

