from flask import Blueprint, jsonify, request
from app import db
from models.bank_account import BankAccount, BankTransaction
from models.expense import Expense
#from services.bank_import_service import
from datetime import datetime, date

bank_bp = Blueprint('bank', __name__)

#@bank_bp.route('/gmail/v1/users/{userId}/profile', methods=['GET'])

































#@bank_bp.get('/bank_accounts')

#@bank_bp.post('/bank_accounts')

#@bank_bp.patch('/bank_accounts/<int:id>')

#@bank_bp.delete('/bank_accounts/<int:id>')

#@bank_bp.post('/bank_accounts/<int:id>/import')

#@bank_bp.get('/bank_transactions')

#@bank_bp.post('/bank_transactions/<int:id>/match')

#@bank_bp.post('/bank_transactions/<int:id>/create_expense')

#@bank_bp.post('/bank_transactions/<int:id>/ignore')

#@bank_bp.post('/bank_transactions/auto_categorize')
