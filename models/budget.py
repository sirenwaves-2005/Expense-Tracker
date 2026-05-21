from app import db
from functools import partial
from datetime import datetime, timezone

class Budget(db.Model):
    __tablename__ = 'budgets'
    __table_args__ = (db.UniqueConstraint('month', 'year', 'category_id'),)

    id           = db.Column(db.Integer, primary_key=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    month        = db.Column(db.Integer, nullable=False)
    year         = db.Column(db.Integer, nullable=False)
    category_id  = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at   = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))
    updated_at   = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc), onupdate=partial(datetime.now, tz=timezone.utc))

    category = db.relationship('Category', backref='budgets', lazy=True)

    @property
    def amount(self):
        return round(self.amount_cents / 100, 2)
