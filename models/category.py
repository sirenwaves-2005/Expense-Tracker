from app import db
from functools import partial
from datetime import datetime, timezone

class Category(db.Model):
    __tablename__ = 'categories'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    icon       = db.Column(db.String(10), default='💰')
    color      = db.Column(db.String(20), default='#6366f1')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))
    updated_at = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc), onupdate=partial(datetime.now, tz=timezone.utc))

    expenses = db.relationship('Expense', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'icon':       self.icon,
            'color':      self.color,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
        }
