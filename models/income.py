from app import db
from functools import partial
from datetime import datetime, date, timezone

class Income(db.Model):
    __tablename__ = 'incomes'

    id           = db.Column(db.Integer,  primary_key=True)
    amount_cents = db.Column(db.Integer,  nullable=False)
    description  = db.Column(db.String(255), nullable=False)
    source       = db.Column(db.String(100))
    income_date  = db.Column(db.Date,     nullable=False, default=date.today)
    created_at   = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))
    updated_at   = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc), onupdate=partial(datetime.now, tz=timezone.utc))

    @property
    def amount(self):
        return round(self.amount_cents / 100, 2)

    def to_dict(self):
        return {
            'id':           self.id,
            'amount':       self.amount,
            'amount_cents': self.amount_cents,
            'description':  self.description,
            'source':       self.source,
            'income_date':  self.income_date.isoformat(),
            'created_at':   self.created_at.isoformat(),
        }
