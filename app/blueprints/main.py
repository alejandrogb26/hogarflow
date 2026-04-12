from flask import Blueprint, render_template, redirect, url_for
from datetime import date
from app.utils import (
    get_current_balance,
    get_month_summary,
    get_recent_movements,
    get_monthly_totals,
    get_expense_by_category,
    get_period_start,
    set_period_start,
    month_name,
)

main = Blueprint("main", __name__)


@main.route("/")
def dashboard():
    today = date.today()
    balance = get_current_balance()
    month_summary = get_month_summary()
    recent_movements = get_recent_movements(limit=8)
    monthly_totals = get_monthly_totals(months=6)
    expense_by_cat = get_expense_by_category()
    period_start = get_period_start()

    return render_template(
        "main/dashboard.html",
        balance=balance,
        month_summary=month_summary,
        recent_movements=recent_movements,
        monthly_totals=monthly_totals,
        expense_by_cat=expense_by_cat,
        period_start=period_start,
        today=today,
        month_name=month_name(today.month),
        current_year=today.year,
        current_month=today.month,
    )


@main.route("/nuevo-periodo", methods=["POST"])
def new_period():
    set_period_start(date.today())
    return redirect(url_for("main.dashboard"))
