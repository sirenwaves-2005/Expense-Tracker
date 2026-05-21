from flask import Blueprint, jsonify, request, current_app
from app import db
from models.budget import Budget
from models.expense import Expense
from datetime import date

budget_bp = Blueprint('budget', __name__)

def _budget_to_dict(b):
    from sqlalchemy import and_
    y, m = b.year, b.month
    start = date(y, m, 1)
    end   = date(y+1,1,1) if m==12 else date(y,m+1,1)
    q = Expense.query.filter(Expense.status=='approved',
                             Expense.expense_date>=start, Expense.expense_date<end)
    if b.category_id:
        q = q.filter(Expense.category_id==b.category_id)
    spent = sum(e.amount_cents for e in q.all())
    pct   = round(spent * 100 / b.amount_cents, 1) if b.amount_cents else 0
    threshold = current_app.config['BUDGET_ALERT_THRESHOLD']
    return {
        'id':            b.id,
        'amount':        b.amount,
        'amount_cents':  b.amount_cents,
        'month':         b.month,
        'year':          b.year,
        'category_id':   b.category_id,
        'category':      b.category.to_dict() if b.category else None,
        'spent_cents':   spent,
        'spent':         round(spent/100, 2),
        'remaining':     round((b.amount_cents - spent)/100, 2),
        'percent_used':  pct,
        'alert':         pct >= threshold,
    }

#@budget_bp.get('/budgets')


#@budget_bp.post('/budgets')


#@budget_bp.delete('/budgets/<int:id>')

