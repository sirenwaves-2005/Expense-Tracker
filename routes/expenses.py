from flask import Blueprint, jsonify, request, current_app
from app import db
from models.expense import Expense
from models.category import Category
from datetime import date, datetime, timezone
import math

expenses_bp = Blueprint('expenses', __name__)

def _check_approval(expense):
    # Only flag as pending if above ₹50,000 (5,000,000 cents) for manual entries
    # Default threshold of ₹50 was too low — most expenses would be flagged
    threshold = current_app.config.get('APPROVAL_THRESHOLD_CENTS', 5000000)
    if expense.amount_cents >= threshold and expense.source == 'manual':
        expense.status = 'pending'

# GET /expenses
@expenses_bp.route('/expenses', methods=['GET'])
def list_expenses():
    q = Expense.query.filter()

    if request.args.get('year') and request.args.get('month'):
        y, m = int(request.args['year']), int(request.args['month'])
        start = date(y, m, 1)
        # last day of month
        if m == 12:
            end = date(y + 1, 1, 1)
        else:
            end = date(y, m + 1, 1)
        q = q.filter(Expense.expense_date >= start, Expense.expense_date < end)

    if request.args.get('category_id'):
        q = q.filter_by(category_id=int(request.args['category_id']))
    if request.args.get('status'):
        q = q.filter_by(status=request.args['status'])
    if request.args.get('source'):
        q = q.filter_by(source=request.args['source'])
    if request.args.get('search'):
        term = f"%{request.args['search']}%"
        q = q.filter(
            db.or_(Expense.description.ilike(term), Expense.merchant.ilike(term))
        )

    q = q.order_by(Expense.expense_date.desc(), Expense.created_at.desc())

    total    = q.count()
    page     = max(int(request.args.get('page', 1)), 1)
    per_page = min(max(int(request.args.get('per_page', 20)), 1), 100)
    expenses = q.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        expenses=    [e.to_dict() for e in expenses],
        total=       total,
        page=        page,
        per_page=    per_page,
        total_pages= math.ceil(total / per_page)
    )

# GET /expenses/summary
@expenses_bp.route('/expenses/summary', methods=['GET'])
def summary():
    y = int(request.args.get('year',  date.today().year))
    m = int(request.args.get('month', date.today().month))
    start = date(y, m, 1)
    end   = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    rows = (
        db.session.query(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            db.func.sum(Expense.amount_cents).label('total_cents'),
            db.func.count(Expense.id).label('count')
        )
        .join(Expense, Expense.category_id == Category.id)
        .filter(
            Expense.status == 'approved',
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
        .group_by(Category.id)
        .order_by(db.desc('total_cents'))
        .all()
    )

    total_cents = sum(r.total_cents or 0 for r in rows)
    return jsonify(
        year=y, month=m,
        total=       round(total_cents / 100, 2),
        total_cents= total_cents,
        categories= [{
            'category_id':   r.id,
            'category_name': r.name,
            'icon':          r.icon,
            'color':         r.color,
            'total':         round((r.total_cents or 0) / 100, 2),
            'total_cents':   r.total_cents or 0,
            'count':         r.count,
            'percentage':    round((r.total_cents or 0) * 100 / total_cents, 1) if total_cents else 0
        } for r in rows]
    )

# GET /expenses/<id>
@expenses_bp.route('/expenses/<int:id>', methods=['GET'])
def get_expense(id):
    e = Expense.query.get_or_404(id)
    return jsonify(e.to_dict())

# POST /expenses
@expenses_bp.post('/expenses')
def create_expense():
    data = request.get_json() or {}
    if not data.get('description'):
        return jsonify(error='description is required'), 422

    amount_cents = data.get('amount_cents') or int(round(float(data.get('amount', 0)) * 100))
    if amount_cents <= 0:
        return jsonify(error='amount must be greater than 0'), 422

    expense_date = date.fromisoformat(data['expense_date']) if data.get('expense_date') else date.today()

    # Accept status from frontend: 'approved' means paid, 'pending' means not paid yet
    raw_status = data.get('status', 'approved')
    status = raw_status if raw_status in ('approved', 'pending') else 'approved'

    e = Expense(
        amount_cents= amount_cents,
        description=  data['description'],
        merchant=     data.get('merchant'),
        expense_date= expense_date,
        category_id=  data.get('category_id'),
        notes=        data.get('notes'),
        source=       'manual',
        status=       status,
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201

# PATCH /expenses/<id>
@expenses_bp.route('/expenses/<int:id>', methods=['PATCH'])
def update_expense(id):
    e    = Expense.query.get_or_404(id)
    data = request.get_json() or {}

    for field in ('description', 'merchant', 'notes', 'category_id'):
        if field in data:
            setattr(e, field, data[field])

    if 'amount_cents' in data:
        e.amount_cents = int(data['amount_cents'])
    elif 'amount' in data:
        e.amount_cents = int(round(float(data['amount']) * 100))

    if 'expense_date' in data:
        e.expense_date = date.fromisoformat(data['expense_date'])

    if 'status' in data:
        raw_status = data['status']
        e.status = raw_status if raw_status in ('approved', 'pending') else e.status
    
    e.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(e.to_dict())

# DELETE /expenses/<id>
@expenses_bp.route('/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    e = Expense.query.get_or_404(id)
    import os
    if e.receipt_path and os.path.exists(e.receipt_path):
        os.remove(e.receipt_path)
    db.session.delete(e)
    db.session.commit()
    return jsonify(message='Expense deleted', id=id)
