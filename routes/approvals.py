from flask import Blueprint, jsonify, request, current_app
from app import db
from models.expense import Expense
from datetime import datetime

approvals_bp = Blueprint('approvals', __name__)

@approvals_bp.route('/approvals', methods=['GET'])          #get api of approval is created
def list_pending():
    pending   = Expense.query.filter_by(status='pending').order_by(Expense.created_at.desc()).all()
    threshold = current_app.config['APPROVAL_THRESHOLD_CENTS']
    return jsonify(
        pending_count=len(pending), 
        threshold=threshold/100, 
        pending_expenses=[e.to_dict() for e in pending]
    )

@approvals_bp.route('/approvals/<int:id>/approve', methods=['POST'])        
def approve(id):
    e = Expense.query.get_or_404(id)
    if e.status != 'pending': 
        return jsonify(
            error='Expense is not pending'), 422
    data = request.get_json() or {}
    if data.get('note'):
        e.notes = ' | '.join(filter(None, [e.notes, data['note']]))
    e.status = 'approved'; e.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(
        message='Expense approved', 
        expense=e.to_dict()
    )

@approvals_bp.route('/approvals/bulk', methods=['POST'])
def bulk():
    data   = request.get_json() or {}
    action = data.get('action')
    ids    = [int(i) for i in data.get('ids', [])]
    if action not in ('approve','reject'): return jsonify(error='action must be approve or reject'), 400
    if not ids: return jsonify(error='ids required'), 400
    new_status = 'approved' if action == 'approve' else 'rejected'
    updated = Expense.query.filter(Expense.id.in_(ids), Expense.status=='pending')\
                           .update({'status': new_status}, synchronize_session=False)
    db.session.commit()
    return jsonify(action=action, updated=updated, ids=ids)
