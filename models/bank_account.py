from app import db
from functools import partial
from datetime import datetime, timezone

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'

    id             = db.Column(db.Integer,  primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    institution    = db.Column(db.String(100))
    account_type   = db.Column(db.String(20), default='checking')
    last_four      = db.Column(db.String(4))
    last_synced_at = db.Column(db.DateTime)
    created_at     = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))
    updated_at     = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc), onupdate=partial(datetime.now, tz=timezone.utc))

    transactions = db.relationship('BankTransaction', backref='bank_account', lazy=True)

    def to_dict(self):
        return {
            'id':             self.id,
            'name':           self.name,
            'institution':    self.institution,
            'account_type':   self.account_type,
            'last_four':      self.last_four,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at':     self.created_at.isoformat(),
        }


class BankTransaction(db.Model):
    __tablename__ = 'bank_transactions'

    id              = db.Column(db.Integer,  primary_key=True)
    bank_account_id = db.Column(db.Integer,  db.ForeignKey('bank_accounts.id'))
    tx_ref          = db.Column(db.String(100), nullable=False, unique=True)
    amount_cents    = db.Column(db.Integer,  nullable=False)
    description     = db.Column(db.String(255))
    merchant        = db.Column(db.String(255))
    tx_date         = db.Column(db.Date,     nullable=False)
    tx_type         = db.Column(db.String(10),  default='debit')   # debit|credit
    import_status   = db.Column(db.String(20),  default='pending') # pending|matched|ignored
    expense_id      = db.Column(db.Integer,  db.ForeignKey('expenses.id'), nullable=True)
    created_at      = db.Column(db.DateTime, default=partial(datetime.now, tz=timezone.utc))

    def to_dict(self):
        return {
            'id':              self.id,
            'bank_account_id': self.bank_account_id,
            'tx_ref':          self.tx_ref,
            'amount':          round(self.amount_cents / 100, 2),
            'amount_cents':    self.amount_cents,
            'description':     self.description,
            'merchant':        self.merchant,
            'tx_date':         self.tx_date.isoformat(),
            'tx_type':         self.tx_type,
            'import_status':   self.import_status,
            'expense_id':      self.expense_id,
            'created_at':      self.created_at.isoformat(),
        }
