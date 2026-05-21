from flask import Blueprint, jsonify, request
from app import db
from models.income import Income
from models.expense import Expense
from datetime import date, datetime

balance_bp = Blueprint('balance', __name__)

def _compute_balance(as_of=None):
    as_of = as_of or date.today()
    total_income   = db.session.query(db.func.sum(Income.amount_cents))\
                       .filter(Income.income_date <= as_of).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount_cents))\
                       .filter(Expense.status=='approved', Expense.expense_date <= as_of).scalar() or 0
    return total_income, total_expenses

@balance_bp.get('/balance')
def get_balance():
    as_of = date.fromisoformat(request.args['as_of']) if request.args.get('as_of') else date.today()
    income, expenses = _compute_balance(as_of)
    balance = income - expenses

    y, m = as_of.year, as_of.month
    start = date(y, m, 1)
    end   = date(y+1,1,1) if m==12 else date(y,m+1,1)
    month_exp = db.session.query(db.func.sum(Expense.amount_cents))\
                  .filter(Expense.status=='approved',
                          Expense.expense_date>=start, Expense.expense_date<end).scalar() or 0
    month_inc = db.session.query(db.func.sum(Income.amount_cents))\
                  .filter(Income.income_date>=start, Income.income_date<end).scalar() or 0

    return jsonify(
        balance=        round(balance/100, 2),
        balance_cents=  balance,
        total_income=   round(income/100, 2),
        total_expenses= round(expenses/100, 2),
        as_of=          as_of.isoformat(),
        this_month=dict(year=y, month=m,
                        income=round(month_inc/100,2),
                        expenses=round(month_exp/100,2),
                        net=round((month_inc-month_exp)/100,2))
    )

#@balance_bp.get('/incomes')

#@balance_bp.post('/incomes')

#@balance_bp.delete('/incomes/<int:id>')
