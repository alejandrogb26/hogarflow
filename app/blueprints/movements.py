from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import date
from decimal import Decimal, InvalidOperation
from app import db
from app.models import Movement, Category

movements = Blueprint("movements", __name__)


def _validate_movement_form(form):
    """
    Validate movement form data. Returns (data_dict, errors_list).
    Manual validation chosen over Flask-WTF to keep dependencies lean and
    because these forms are simple enough not to justify the overhead.
    """
    errors = []
    data = {}

    # Date
    raw_date = form.get("date", "").strip()
    if not raw_date:
        errors.append("La fecha es obligatoria.")
    else:
        try:
            data["date"] = date.fromisoformat(raw_date)
        except ValueError:
            errors.append("Formato de fecha inválido.")

    # Amount
    raw_amount = form.get("amount", "").strip().replace(",", ".")
    if not raw_amount:
        errors.append("El importe es obligatorio.")
    else:
        try:
            amount = Decimal(raw_amount)
            if amount == 0:
                errors.append("El importe no puede ser cero.")
            data["amount"] = amount
        except InvalidOperation:
            errors.append("El importe debe ser un número válido.")

    # Category
    raw_cat = form.get("category_id", "").strip()
    if not raw_cat:
        errors.append("La categoría es obligatoria.")
    else:
        try:
            cat_id = int(raw_cat)
            cat = db.session.get(Category, cat_id)
            if not cat:
                errors.append("Categoría no válida.")
            else:
                data["category_id"] = cat_id
        except (ValueError, TypeError):
            errors.append("Categoría no válida.")

    # Concept (optional)
    data["concept"] = form.get("concept", "").strip() or None

    return data, errors


@movements.route("/")
def index():
    # Filtering by month/year (optional query params)
    today = date.today()
    year = request.args.get("year", type=int, default=today.year)
    month = request.args.get("month", type=int, default=today.month)
    category_id = request.args.get("category_id", type=int)

    query = Movement.query

    if year and month:
        from sqlalchemy import extract
        query = query.filter(
            extract("year", Movement.date) == year,
            extract("month", Movement.date) == month,
        )

    if category_id:
        query = query.filter(Movement.category_id == category_id)

    page = request.args.get("page", 1, type=int)
    pagination = (
        query.order_by(Movement.date.desc(), Movement.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )

    categories = Category.query.order_by(Category.name).all()

    # Build month selector data (last 24 months)
    from app.utils import month_name as mn
    months_range = []
    y, m = today.year, today.month
    for _ in range(24):
        months_range.append({"year": y, "month": m, "label": f"{mn(m)} {y}"})
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    return render_template(
        "movements/index.html",
        pagination=pagination,
        movements=pagination.items,
        categories=categories,
        selected_year=year,
        selected_month=month,
        selected_category=category_id,
        months_range=months_range,
    )


@movements.route("/nuevo", methods=["GET", "POST"])
def create():
    categories = Category.query.order_by(Category.name).all()

    if not categories:
        flash("Debes crear al menos una categoría antes de registrar movimientos.", "warning")
        return redirect(url_for("categories.create"))

    if request.method == "POST":
        data, errors = _validate_movement_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "movements/form.html",
                categories=categories,
                form_data=request.form,
                action="create",
            )

        movement = Movement(**data)
        db.session.add(movement)
        db.session.commit()
        flash("Movimiento registrado correctamente.", "success")
        return redirect(url_for("movements.index"))

    return render_template(
        "movements/form.html",
        categories=categories,
        form_data={"date": date.today().isoformat()},
        action="create",
    )


@movements.route("/<int:movement_id>/editar", methods=["GET", "POST"])
def edit(movement_id):
    movement = db.get_or_404(Movement, movement_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        data, errors = _validate_movement_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "movements/form.html",
                categories=categories,
                form_data=request.form,
                movement=movement,
                action="edit",
            )

        for key, value in data.items():
            setattr(movement, key, value)
        db.session.commit()
        flash("Movimiento actualizado correctamente.", "success")
        return redirect(url_for("movements.index"))

    form_data = {
        "date": movement.date.isoformat(),
        "amount": str(movement.amount),
        "category_id": movement.category_id,
        "concept": movement.concept or "",
    }
    return render_template(
        "movements/form.html",
        categories=categories,
        form_data=form_data,
        movement=movement,
        action="edit",
    )


@movements.route("/<int:movement_id>/borrar", methods=["POST"])
def delete(movement_id):
    movement = db.get_or_404(Movement, movement_id)
    db.session.delete(movement)
    db.session.commit()
    flash("Movimiento eliminado.", "info")
    return redirect(url_for("movements.index"))
