from app import create_app

# Crée l'application via la factory définie dans app/__init__.py
app = create_app()

if __name__ == "__main__":
    # debug=True pour le développement (rechargement auto)
    app.run(debug=True)
