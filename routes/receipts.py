from flask import Blueprint, jsonify, request, current_app
from app import db
from models.expense import Expense
#from services.ocr_service import extract as ocr_extract
#from services.ocr_service import process_receipt
import os, uuid

receipts_bp = Blueprint('receipts', __name__)

ALLOWED = {'image/jpeg','image/png','image/jpg','application/pdf'}

def _save_file(file):
    ext      = os.path.splitext(file.filename)[1].lower()
    filename = f"receipt_{uuid.uuid4().hex}{ext}"
    folder   = current_app.config['UPLOAD_FOLDER']
    path     = os.path.join(folder, filename)
    file.save(path)
    return path, filename

@receipts_bp.post('/receipts/upload')
def upload_receipt():
    if 'file' not in request.files:
        return jsonify(error='No file uploaded'), 400
    file = request.files['file']
    if file.content_type not in ALLOWED:
        return jsonify(error='Unsupported file type', allowed=list(ALLOWED)), 415

    path, filename = _save_file(file)
    ocr_result = {}
    if request.form.get('run_ocr', 'true') != 'false':
        ocr_result = ocr_extract(path)

    if request.form.get('expense_id'):
        e = Expense.query.get_or_404(int(request.form['expense_id']))
        if e.receipt_path and os.path.exists(e.receipt_path):
            os.remove(e.receipt_path)
        e.receipt_path     = path
        e.receipt_filename = filename
        db.session.commit()

    return jsonify(filename=filename, url=f'/uploads/{filename}',
                   expense_id=request.form.get('expense_id'), ocr=ocr_result), 201

@receipts_bp.post('/receipts/scan')
def scan_receipt():
    if 'file' not in request.files:
        return jsonify(error='No file uploaded'), 400
    file = request.files['file']
    if file.content_type not in ALLOWED:
        return jsonify(error='Unsupported file type'), 415

    path, filename = _save_file(file)
    ocr_result     = ocr_extract(path)

    draft = dict(
        description=      ocr_result.get('merchant') or 'Scanned receipt',
        merchant=         ocr_result.get('merchant'),
        amount_cents=     ocr_result.get('amount_cents'),
        expense_date=     ocr_result.get('date'),
        source=           'ocr',
        status=           'pending',
        receipt_path=     path,
        receipt_filename= filename,
    )

    if (ocr_result.get('confidence', 0) >= 0.7 and (ocr_result.get('amount_cents') or 0) > 0):
        from datetime import date
        e = Expense(
            amount_cents=     draft['amount_cents'],
            description=      draft['description'],
            merchant=         draft['merchant'],
            expense_date=     date.fromisoformat(draft['expense_date']) if draft['expense_date'] else date.today(),
            source=           'ocr',
            status=           'pending',
            receipt_path=     path,
            receipt_filename= filename,
        )
        db.session.add(e)
        db.session.commit()
        return jsonify(auto_created=True, expense=e.to_dict(), ocr=ocr_result), 201

    return jsonify(auto_created=False, draft=draft, ocr=ocr_result,
                   hint='Review and confirm before saving')

@receipts_bp.delete('/receipts/<filename>')
def delete_receipt(filename):
    filename = filename.replace('..', '')
    path     = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return jsonify(error='File not found'), 404
    Expense.query.filter_by(receipt_filename=filename)\
                 .update({'receipt_path': None, 'receipt_filename': None})
    db.session.commit()
    os.remove(path)
    return jsonify(message='Receipt deleted')
