import os
from app import create_app, db
from app.models import Category, Movement

app = create_app(os.environ.get("FLASK_ENV", "default"))


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Category": Category, "Movement": Movement}


@app.cli.command("seed")
def seed_db():
    """Seed the database with example categories."""
    default_categories = [
        {"name": "Nómina",        "color": "#10b981"},
        {"name": "Alquiler",      "color": "#ef4444"},
        {"name": "Comunidad",     "color": "#f59e0b"},
        {"name": "Luz",           "color": "#fbbf24"},
        {"name": "Agua",          "color": "#3b82f6"},
        {"name": "Gas",           "color": "#f97316"},
        {"name": "Coche",         "color": "#8b5cf6"},
        {"name": "Supermercado",  "color": "#14b8a6"},
        {"name": "Restaurantes",  "color": "#ec4899"},
        {"name": "Ocio",          "color": "#6366f1"},
        {"name": "Salud",         "color": "#84cc16"},
        {"name": "Seguros",       "color": "#64748b"},
    ]
    added = 0
    for cat_data in default_categories:
        if not Category.query.filter_by(name=cat_data["name"]).first():
            db.session.add(Category(**cat_data))
            added += 1
    db.session.commit()
    print(f"✅  {added} categorías añadidas.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
