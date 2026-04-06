from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import func, extract, case
from app import db
from app.models import Movement, Category


# ── Template filters ──────────────────────────────────────────────────────────

def format_currency(value):
    """Format a number as euro currency string."""
    try:
        v = Decimal(str(value))
        sign = "+" if v > 0 else ""
        return f"{sign}{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def format_date(value):
    """Format a date object to dd/mm/yyyy."""
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return str(value)


# ── Business logic queries ────────────────────────────────────────────────────

def get_current_balance():
    """Compute balance as SUM of all movement amounts."""
    result = db.session.query(func.sum(Movement.amount)).scalar()
    return Decimal(str(result)) if result is not None else Decimal("0.00")


def get_month_summary(year=None, month=None):
    """Return income, expenses and net for a given month (defaults to current)."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    q = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (Movement.amount > 0, Movement.amount),
                    else_=0
                )
            ),
            0
        ).label("income"),
        func.coalesce(
            func.sum(
                case(
                    (Movement.amount < 0, Movement.amount),
                    else_=0
                )
            ),
            0
        ).label("expenses"),
        func.coalesce(func.sum(Movement.amount), 0).label("net"),
    ).filter(
        extract("year", Movement.date) == year,
        extract("month", Movement.date) == month,
    )

    row = q.one()

    return {
        "income": Decimal(str(row.income)) if row.income else Decimal("0.00"),
        "expenses": Decimal(str(row.expenses)) if row.expenses else Decimal("0.00"),
        "net": Decimal(str(row.net)) if row.net else Decimal("0.00"),
        "year": year,
        "month": month,
    }


def get_recent_movements(limit=8):
    """Return the most recent movements ordered by date then creation time."""
    return (
        Movement.query.order_by(Movement.date.desc(), Movement.created_at.desc())
        .limit(limit)
        .all()
    )


def get_monthly_totals(months=6):
    """
    Return last N months with income, expenses and net per month.
    Used for the bar/line chart.
    """
    rows = (
        db.session.query(
            extract("year", Movement.date).label("year"),
            extract("month", Movement.date).label("month"),
            func.coalesce(
                func.sum(
                    case(
                        (Movement.amount > 0, Movement.amount),
                        else_=0
                    )
                ),
                0
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (Movement.amount < 0, Movement.amount),
                        else_=0
                    )
                ),
                0
            ).label("expenses"),
            func.coalesce(func.sum(Movement.amount), 0).label("net"),
        )
        .group_by(
            extract("year", Movement.date),
            extract("month", Movement.date),
        )
        .order_by(
            extract("year", Movement.date).desc(),
            extract("month", Movement.date).desc(),
        )
        .limit(months)
        .all()
    )

    result = []
    for r in reversed(rows):
        result.append({
            "label": f"{int(r.month):02d}/{int(r.year)}",
            "income": float(r.income or 0),
            "expenses": abs(float(r.expenses or 0)),
            "net": float(r.net or 0),
        })
    return result


def get_expense_by_category(year=None, month=None):
    """Return total expenses grouped by category for a given month."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    rows = (
        db.session.query(
            Category.name,
            Category.color,
            func.coalesce(func.sum(Movement.amount), 0).label("total"),
        )
        .join(Movement, Movement.category_id == Category.id)
        .filter(
            Movement.amount < 0,
            extract("year", Movement.date) == year,
            extract("month", Movement.date) == month,
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Movement.amount).asc())
        .all()
    )

    return [
        {
            "category": r.name,
            "color": r.color,
            "total": abs(float(r.total)),
        }
        for r in rows
    ]


def get_balance_evolution(months=6):
    """
    Return running balance for each of the last N months.
    Useful for a line chart showing wealth trend.
    """
    monthly = get_monthly_totals(months)
    result = []
    cumulative = Decimal("0.00")

    for m in monthly:
        cumulative += Decimal(str(m["net"]))
        result.append({"label": m["label"], "balance": float(cumulative)})

    return result


def get_income_vs_expense_totals():
    """Total income and total expenses across all time — for the donut chart."""
    row = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (Movement.amount > 0, Movement.amount),
                    else_=0
                )
            ),
            0
        ).label("income"),
        func.coalesce(
            func.sum(
                case(
                    (Movement.amount < 0, Movement.amount),
                    else_=0
                )
            ),
            0
        ).label("expenses"),
    ).one()

    return {
        "income": float(row.income or 0),
        "expenses": abs(float(row.expenses or 0)),
    }


MONTH_NAMES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def month_name(month_num):
    return MONTH_NAMES_ES.get(int(month_num), str(month_num))