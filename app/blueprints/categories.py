from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Category

categories = Blueprint("categories", __name__)

DEFAULT_COLORS = [
    "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#EC4899", "#14B8A6", "#F97316",
    "#6366F1", "#84CC16",
]


def _validate_category_form(form, exclude_id=None):
    errors = []
    data = {}

    name = form.get("name", "").strip()
    if not name:
        errors.append("El nombre de la categoría es obligatorio.")
    elif len(name) > 80:
        errors.append("El nombre no puede superar los 80 caracteres.")
    else:
        # Unique check
        q = Category.query.filter(Category.name.ilike(name))
        if exclude_id:
            q = q.filter(Category.id != exclude_id)
        if q.first():
            errors.append(f"Ya existe una categoría llamada '{name}'.")
        data["name"] = name

    color = form.get("color", "").strip()
    if not color or not color.startswith("#") or len(color) != 7:
        color = DEFAULT_COLORS[0]
    data["color"] = color

    return data, errors


@categories.route("/")
def index():
    cats = Category.query.order_by(Category.name).all()
    return render_template("categories/index.html", categories=cats)


@categories.route("/nueva", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data, errors = _validate_category_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "categories/form.html",
                form_data=request.form,
                action="create",
                colors=DEFAULT_COLORS,
            )
        cat = Category(**data)
        db.session.add(cat)
        db.session.commit()
        flash(f"Categoría '{cat.name}' creada correctamente.", "success")
        return redirect(url_for("categories.index"))

    return render_template(
        "categories/form.html",
        form_data={},
        action="create",
        colors=DEFAULT_COLORS,
    )


@categories.route("/<int:category_id>/editar", methods=["GET", "POST"])
def edit(category_id):
    cat = db.get_or_404(Category, category_id)

    if request.method == "POST":
        data, errors = _validate_category_form(request.form, exclude_id=category_id)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "categories/form.html",
                form_data=request.form,
                category=cat,
                action="edit",
                colors=DEFAULT_COLORS,
            )
        cat.name = data["name"]
        cat.color = data["color"]
        db.session.commit()
        flash(f"Categoría actualizada correctamente.", "success")
        return redirect(url_for("categories.index"))

    return render_template(
        "categories/form.html",
        form_data={"name": cat.name, "color": cat.color},
        category=cat,
        action="edit",
        colors=DEFAULT_COLORS,
    )


@categories.route("/<int:category_id>/borrar", methods=["POST"])
def delete(category_id):
    """
    Deletion strategy: BLOCK if the category has associated movements.
    Rationale: silently reassigning movements would corrupt historical data
    and confuse the user. Blocking is honest, safe, and forces a deliberate
    decision. The error message guides the user clearly.
    """
    cat = db.get_or_404(Category, category_id)
    if cat.movement_count > 0:
        flash(
            f"No puedes eliminar '{cat.name}' porque tiene "
            f"{cat.movement_count} movimiento(s) asociado(s). "
            "Reasigna o elimina esos movimientos primero.",
            "error",
        )
        return redirect(url_for("categories.index"))

    db.session.delete(cat)
    db.session.commit()
    flash(f"Categoría '{cat.name}' eliminada.", "info")
    return redirect(url_for("categories.index"))
