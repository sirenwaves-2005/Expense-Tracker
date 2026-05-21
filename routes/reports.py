from flask import Blueprint, jsonify, request, Response
from app import db
from models.expense import Expense
from models.budget import Budget
from models.category import Category
from services.report_service import (
    get_monthly_expenses,
    predict_expenses,
    detect_anomalies,
    get_spending_trend
)
from datetime import date
import csv, io

reports_bp = Blueprint('reports', __name__)


# ---------------- HELPER ----------------
def _month_range(y, m):
    start = date(y, m, 1)
    end = date(y+1,1,1) if m==12 else date(y,m+1,1)
    return start, end


# ---------------- DASHBOARD ----------------
@reports_bp.route('/reports/dashboard', methods=['GET'])
def dashboard():
    y = int(request.args.get('year', date.today().year))
    m = int(request.args.get('month', date.today().month))
    start, end = _month_range(y, m)

    monthly = get_monthly_expenses(db, 12, y, m)
    trend = [
        {
            'year': item['year'],
            'month': item['month'],
            'expenses': item['total']
        }
        for item in monthly
    ]

    # ---------------- CATEGORY BREAKDOWN ----------------
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

    # ---------------- TOP MERCHANTS ----------------
    top_merchants = (
        db.session.query(
            Expense.merchant,
            db.func.sum(Expense.amount_cents).label('total_cents'),
            db.func.count(Expense.id).label('count')
        )
        .filter(
            Expense.status == 'approved',
            Expense.merchant != None,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
        .group_by(Expense.merchant)
        .order_by(db.desc('total_cents'))
        .limit(5)
        .all()
    )

    # ---------------- BUDGETS ----------------
    budgets = Budget.query.filter_by(year=y, month=m).all()

    # ---------------- RECENT ----------------
    recent = (
        Expense.query.filter_by(status='approved')
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .limit(5)
        .all()
    )

    # ---------------- EXTRA SERVICES ----------------
    trend_stats = get_spending_trend(db, y, m)

    return jsonify(
        period={'year': y, 'month': m},
        monthly_trend=trend,
        total_this_month=round(total_cents/100, 2),
        trend_stats=trend_stats,

        category_breakdown=[
            {
                'category_id': r.id,
                'name': r.name,
                'icon': r.icon,
                'color': r.color,
                'total': round((r.total_cents or 0)/100, 2),
                'total_cents': r.total_cents or 0,
                'count': r.count,
                'percentage': round((r.total_cents or 0)*100/total_cents,1) if total_cents else 0
            }
            for r in rows
        ],

        top_merchants=[
            {
                'merchant': r.merchant,
                'total': round(r.total_cents/100,2),
                'count': r.count
            }
            for r in top_merchants
        ],
        recent_expenses=[e.to_dict() for e in recent],
    )


# ---------------- MONTHLY ----------------
@reports_bp.route('/reports/monthly', methods=['GET'])
def monthly():
    y = int(request.args.get('year', date.today().year))
    m = int(request.args.get('month', date.today().month))
    start, end = _month_range(y, m)

    expenses = Expense.query.filter(
        Expense.status=='approved',
        Expense.expense_date>=start,
        Expense.expense_date<end
    ).order_by(Expense.expense_date).all()

    daily = {}
    for e in expenses:
        k = e.expense_date.isoformat()
        daily[k] = round(daily.get(k, 0) + e.amount_cents/100, 2)

    return jsonify(
        year=y,
        month=m,
        total=round(sum(e.amount_cents for e in expenses)/100, 2),
        count=len(expenses),
        daily_totals=[{'date':d,'total':t} for d,t in sorted(daily.items())],
        expenses=[e.to_dict() for e in expenses]
    )


# ---------------- EXPORT ----------------
def _get_month_expenses(y, m):
    start, end = _month_range(y, m)
    return Expense.query.filter(
        Expense.status=='approved',
        Expense.expense_date>=start,
        Expense.expense_date<end
    ).order_by(Expense.expense_date).all()


@reports_bp.route('/reports/export.csv', methods=['GET'])
def export_csv():
    y = int(request.args.get('year', date.today().year))
    m = int(request.args.get('month', date.today().month))

    expenses = _get_month_expenses(y, m)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date','Description','Merchant','Category','Amount','Status'])

    for e in expenses:
        writer.writerow([
            e.expense_date,
            e.description,
            e.merchant,
            e.category.name if e.category else '',
            e.amount,
            e.status
        ])

    return Response(output.getvalue(), mimetype='text/csv')

# ---------------- TREND ----------------
@reports_bp.route('/reports/trend', methods=['GET'])
def get_trend():
    y = int(request.args.get('year', date.today().year))
    m = int(request.args.get('month', date.today().month))

    data = get_monthly_expenses(db, 12, y, m)

    return jsonify({
        "mode": "monthly",
        "data": [
            {
                "label": f"{item['month']}/{item['year']}",
                "value": round(item['total'], 2)
            }
            for item in data
        ]
    })


# ---------------- PREDICTION ----------------
@reports_bp.route('/reports/prediction', methods=['GET'])
def get_prediction():
    months_ahead = int(request.args.get('months_ahead', 1))
    return jsonify(predict_expenses(db, months_ahead=months_ahead))


# ---------------- ANOMALIES ----------------
@reports_bp.route('/reports/anomalies', methods=['GET'])
def get_anomalies():
    threshold = float(request.args.get('threshold', 2.5))

    result = detect_anomalies(db=db, z_threshold=threshold)

    return jsonify(result)
