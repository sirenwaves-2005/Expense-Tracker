from flask import Blueprint, jsonify, request
from app import db
from models.category import Category
from models.expense import Expense

categories_bp = Blueprint('categories', __name__)

#gets the all category name 
@categories_bp.route('/categories', methods=['GET'])
def list_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify(
        categories=[c.to_dict() for c in cats]
    )

#add new category and checks before adding 
@categories_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify(
            error='name is required'
        ), 422
    if Category.query.filter_by(name=data['name']).first():
        return jsonify(
            error='Category name already exists'
        ), 422
    cat = Category(
        name=data['name'], 
        icon=data.get('icon','📦'), 
        color=data.get('color','#6b7280')
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201

#get category by id
@categories_bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    return jsonify(
        Category.query.get_or_404(id).to_dict()
    )

#partially update the category
@categories_bp.route('/categories/<int:id>', methods=['PATCH'])
def update_category(id):
    cat  = Category.query.get_or_404(id)
    data = request.get_json() or {}
    for field in ('name', 'icon', 'color'):
        if field in data:
            setattr(cat, field, data[field])
    db.session.commit()
    return jsonify(cat.to_dict())

#delete the category
@categories_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.is_default:
        return jsonify(error='Cannot delete a default category'), 422
    count = Expense.query.filter_by(category_id=cat.id).count()
    if count > 0:
        return jsonify(error='Category has expenses attached', expense_count=count,
                       hint='Reassign expenses before deleting'), 422
    db.session.delete(cat)
    db.session.commit()
    return jsonify(message='Category deleted')
