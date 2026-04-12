from datetime import date, datetime
from decimal import Decimal
from app import db


class Category(db.Model):
    """Expense/income category, user-managed."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default="#3B82F6")  # hex color
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movements = db.relationship("Movement", back_populates="category", lazy="dynamic")

    @property
    def movement_count(self):
        return self.movements.count()

    def __repr__(self):
        return f"<Category {self.name}>"

    def to_dict(self):
        return {"id": self.id, "name": self.name, "color": self.color}


class AppConfig(db.Model):
    """
    Single-row key-value config table.
    Used to store app-wide settings like the current period start date.
    """
    __tablename__ = "app_config"

    key = db.Column("config_key", db.String(80), primary_key=True)
    value = db.Column("config_value", db.String(255), nullable=False)

    @classmethod
    def get(cls, key, default=None):
        row = cls.query.get(key)
        return row.value if row else default

    @classmethod
    def set(cls, key, value):
        row = cls.query.get(key)
        if row:
            row.value = str(value)
        else:
            row = cls(key=key, value=str(value))
            db.session.add(row)
        db.session.commit()


class Movement(db.Model):
    """
    A financial movement (income or expense).

    Design decision on balance:
    We do NOT store balance as a field. Balance is always computed as
    SUM(amount) over all movements. This guarantees consistency: editing
    or deleting any movement automatically reflects in the balance without
    any synchronisation logic. The tradeoff is a slightly heavier query,
    which is negligible for a household app with at most a few thousand rows.
    For very large datasets a materialized view or cached field with triggers
    could be considered, but it would be premature optimisation here.

    Convention: positive amount = income, negative amount = expense.
    """
    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    concept = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    category = db.relationship("Category", back_populates="movements")

    @property
    def is_income(self):
        return Decimal(str(self.amount)) > 0

    @property
    def is_expense(self):
        return Decimal(str(self.amount)) < 0

    @property
    def abs_amount(self):
        return abs(Decimal(str(self.amount)))

    def __repr__(self):
        return f"<Movement {self.date} {self.amount}>"
