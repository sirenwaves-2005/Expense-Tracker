from models.expense import Expense
from datetime import date
import json


#monthly expense
def get_monthly_expenses(db, months_back=12, year=None, month=None):

    if year and month:
        today = date(year, month, 1)
    else:
        today = date.today()

    data = []           #storing monthly results in list

    for i in range(months_back-1, -1, -1):
        mm = today.month - i
        yy = today.year

        while mm <= 0:
            mm += 12
            yy -= 1

        y = yy
        m = mm

        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1)
        else:
            end = date(y, m + 1, 1)

        total_cents = db.session.query(db.func.sum(Expense.amount_cents)) \
            .filter(
                Expense.status.in_(['approved', 'paid']),
                Expense.expense_date >= start,
                Expense.expense_date < end
            ).scalar() or 0

        count = db.session.query(db.func.count(Expense.id)) \
            .filter(
                Expense.status.in_(['approved', 'paid']),
                Expense.expense_date >= start,
                Expense.expense_date < end
            ).scalar() or 0
    
        data.append({
            'year': y,
            'month': m,
            'total': round(total_cents / 100, 2),
            'total_cents': total_cents,
            'count': count
        })

    return data

#prediction
def predict_expenses(db, months_ahead=1, year=None, month=None):
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
    except ImportError:
        return {
            'success': False,
            'error': 'sklearn not installed. Run: pip install scikit-learn',
            'predicted_amount': None,
            'confidence': 0
        }

    # recent data (last 3 months)
    monthly_data = get_monthly_expenses(db, 3, year, month)

    #recent trend= current vs previous
    current = monthly_data[-1]['total']
    prev = monthly_data[-2]['total'] if len(monthly_data) > 1 else current

    # simple trend adjustment, how much did current change wrt previous
    growth = (current - prev) / prev if prev > 0 else 0

    if len(monthly_data) < 3:
        return {
            'success': False,
            'error': 'Insufficient data (need 3+ months)',
            'predicted_amount': None,
            'confidence': 0,
            'reason': f'Only {len(monthly_data)} months of data available'
        }

    amounts = np.array([m['total'] for m in monthly_data]).reshape(-1, 1)       #target values
    months_idx = np.array(range(len(monthly_data))).reshape(-1, 1)              #input values

    model = LinearRegression()
    model.fit(months_idx, amounts)

    #next index 
    next_idx = np.array([[len(monthly_data) + months_ahead - 1]])
    
    # ML prediction
    ml_pred = float(model.predict(next_idx).ravel()[0])

    #protect against current month spikes
    if prev > 0:
        current = min(current, prev * 1.5)

    #controlled growth
    growth = (current - prev) / prev if prev > 0 else 0
    growth = max(min(growth, 0.3), -0.3)

    #recent prediction
    recent_pred = current * (1 + growth)

    #hybrid (more weight to recent)
    predicted = (0.7 * recent_pred) + (0.3 * ml_pred)

    #final safety cap
    predicted = min(predicted, current * 1.3)
    predicted = max(0, predicted)

    r2_score = model.score(months_idx, amounts)
    confidence = max(0, min(1, r2_score))
    uncertainty = (1 - confidence)  # lower confidence = wider range
    margin = predicted * (0.1 + 0.3 * uncertainty)
    
    pred_range = {
        'low': round(predicted - margin, 2),
        'high': round(predicted + margin, 2)
    }
    
    return {
        'success': True,
        'predicted_amount': round(predicted, 2),
        'prediction_range': pred_range,
        'confidence': round(confidence, 3),
        'based_on_months': len(monthly_data),
        'trend': 'increasing' if model.coef_.ravel()[0] > 0 else 'decreasing'
    }


#anamolies
def detect_anomalies(db,z_threshold=2.5, year=None, month=None):
    try:
        import numpy as np
    except ImportError:
        return {
            'success': False,
            'error': 'numpy not installed',
            'anomalies': []
        }

    if year and month:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        expenses = Expense.query.filter(
            Expense.status.in_(['approved', 'paid']),
            Expense.expense_date >= start,
            Expense.expense_date < end
        ).all()
    else:
        expenses = Expense.query.filter(
            Expense.status.in_(['approved', 'paid'])
        ).all()

    if len(expenses) < 5:
        return {
            'success': False,
            'error': 'Insufficient data (need 5+ expenses)',
            'anomalies': [],
            'total_analyzed': len(expenses)
        }

    amounts = np.array([e.amount for e in expenses])
    mean = np.mean(amounts)
    std_dev = np.std(amounts)

    if std_dev == 0:
        return {
            'success': True,
            'anomalies': [],
            'mean': round(mean, 2),
            'std_dev': 0,
            'total_analyzed': len(expenses),
            'reason': 'All expenses are the same amount'
        }

    anomalies = []
    for exp in expenses:
        z = (exp.amount - mean) / std_dev           #zscore calculation for each of the expenses
        if abs(z) > z_threshold:
            deviation_pct = abs((exp.amount - mean) / mean * 100) if mean != 0 else 0
            anomalies.append({
                'id': exp.id,
                'description': exp.description,
                'merchant': exp.merchant or '—',
                'amount': round(exp.amount, 2),
                'date': exp.expense_date.isoformat(),
                'category': exp.category.name if exp.category else 'Other',
                'z_score': round(z, 2),
                'deviation_percent': round(deviation_pct, 1),
                'severity': 'high' if abs(z) > 3.5 else 'moderate'
            })

    anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)

    return {
        'success': True,
        'anomalies': anomalies,
        'mean': round(mean, 2),
        'std_dev': round(std_dev, 2),
        'total_analyzed': len(expenses),
        'anomaly_count': len(anomalies),
        'anomaly_percentage': round(len(anomalies) * 100 / len(expenses), 1)
    }


#spending trend
def get_spending_trend(db, year=None, month=None):

    monthly = get_monthly_expenses(db, 12, year, month)

    if len(monthly) < 2:
        return {
            'this_month': monthly[-1]['total'] if monthly else 0,
            'last_month': 0,
            'trend_direction': 'stable',
            'change_percent': 0,
            'average_monthly': monthly[-1]['total'] if monthly else 0
        }

    this_month = monthly[-1]['total']
    last_month = monthly[-2]['total']
    active_months = [m['total'] for m in monthly if m['total'] > 0]
    avg_monthly = sum(active_months) / len(active_months) if active_months else 0

    if last_month == 0:
        change = 0
        direction = 'stable'
    else:
        change = round((this_month - last_month) / last_month * 100, 1)
        direction = 'up' if change > 5 else ('down' if change < -5 else 'stable')

    return {
        'this_month': round(this_month, 2),
        'last_month': round(last_month, 2),
        'trend_direction': direction,
        'change_percent': change,
        'average_monthly': round(avg_monthly, 2)
    }