from app import db
from functools import partial
from datetime import datetime, date, timezone

class Expense(db.Model):
    __tablename__ = 'expenses'

    id               = db.Column(db.Integer,  primary_key=True)
    amount_cents     = db.Column(db.Integer,  nullable=False)
    description      = db.Column(db.String(255), nullable=False)
    merchant         = db.Column(db.String(255))
    expense_date     = db.Column(db.Date,     nullable=False, default=date.today)
    category_id      = db.Column(db.Integer,  db.ForeignKey('categories.id'))
    status           = db.Column(db.String(20),  default='approved')   # paid \pending
    source           = db.Column(db.String(20),  default='manual')     # manual|bank_import|ocr
    bank_tx_ref      = db.Column(db.String(100))
    receipt_path     = db.Column(db.String(500))
    receipt_filename = db.Column(db.String(255))
    notes            = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))
    updated_at       = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc), onupdate=partial(datetime.now, tz=timezone.utc))

    @property
    def amount(self):
        return round(self.amount_cents / 100, 2)

    def to_dict(self):
        return {
            'id':               self.id,
            'amount':           self.amount,
            'amount_cents':     self.amount_cents,
            'description':      self.description,
            'merchant':         self.merchant,
            'expense_date':     self.expense_date.isoformat(),
            'category_id':      self.category_id,
            'category':         self.category.to_dict() if self.category else None,
            'status':           self.status,
            'source':           self.source,
            'bank_tx_ref':      self.bank_tx_ref,
            'notes':            self.notes,
            'receipt_url':      f'/uploads/{self.receipt_filename}' if self.receipt_filename else None,
            'receipt_filename': self.receipt_filename,
            'created_at':       self.created_at.isoformat(),
            'updated_at':       self.updated_at.isoformat(),
        }
