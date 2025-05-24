from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for flash messages
db = SQLAlchemy(app)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class KitchenOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, ready, completed
    special_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship with order items
    items = db.relationship('KitchenOrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<KitchenOrder {self.id} - Table {self.table_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'status': self.status,
            'special_notes': self.special_notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class KitchenOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('kitchen_order.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    special_instructions = db.Column(db.Text, nullable=True)
    
    # Relationship with recipe
    recipe = db.relationship('Recipe', backref='order_items')
    
    def __repr__(self):
        return f'<KitchenOrderItem {self.id} - Recipe {self.recipe_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'recipe_id': self.recipe_id,
            'recipe_name': self.recipe.name if self.recipe else 'Unknown',
            'quantity': self.quantity,
            'special_instructions': self.special_instructions
        }

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in kg
    expiry_date = db.Column(db.Date, nullable=False)
    autobuy_threshold = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'autobuy_threshold': self.autobuy_threshold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_expiry_status(self):
        today = datetime.now().date()
        days_until_expiry = (self.expiry_date - today).days
        
        if days_until_expiry < 0:
            return "expired"
        elif days_until_expiry <= 5:
            return "hurry"
        else:
            return "ok"

# Create the database and tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Orders.query.all()
    return render_template('orders.html', orders=orders)

@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        name = request.form['name']
        quantity = float(request.form['quantity'])
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
        autobuy_threshold = float(request.form['autobuy_threshold'])
        
        new_order = Orders(
            name=name,
            quantity=quantity,
            expiry_date=expiry_date,
            autobuy_threshold=autobuy_threshold
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        return redirect(url_for('get_orders'))
    
    return render_template('add_order.html')

@app.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
def edit_order(id):
    order = Orders.query.get_or_404(id)
    
    if request.method == 'POST':
        order.name = request.form['name']
        order.quantity = float(request.form['quantity'])
        order.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
        order.autobuy_threshold = float(request.form['autobuy_threshold'])
        
        db.session.commit()
        return redirect(url_for('get_orders'))
    
    return render_template('edit_order.html', order=order)

@app.route('/orders/<int:id>/delete', methods=['POST'])
def delete_order(id):
    order = Orders.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('get_orders'))

@app.route('/orders/<int:id>/reduce', methods=['POST'])
def reduce_order_quantity(id):
    order = Orders.query.get_or_404(id)
    if order.quantity > 0:
        order.quantity -= 1
    db.session.commit()
    return redirect(url_for('get_orders'))

@app.route('/orders/<int:id>/auto-order', methods=['POST'])
def auto_order(id):
    order = Orders.query.get_or_404(id)
    # Add 5 units more than the threshold
    order.quantity = order.autobuy_threshold + 5
    
    # Update the expiry date by adding a random number of days between 5 and 20
    random_days = random.randint(5, 20)
    order.expiry_date = datetime.now().date() + timedelta(days=random_days)
    
    db.session.commit()
    
    flash(f'Order has been sent and received. The old stock has been sent to chef for urgent use or for garbage. New expiry date: {order.expiry_date.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('get_orders'))

# API endpoints for potential frontend integration
@app.route('/api/orders', methods=['GET'])
def get_orders_api():
    orders = Orders.query.all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/orders', methods=['POST'])
def create_order_api():
    data = request.get_json()
    
    try:
        new_order = Orders(
            name=data['name'],
            quantity=float(data['quantity']),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d'),
            autobuy_threshold=float(data['autobuy_threshold'])
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        return jsonify(new_order.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/calculate-price', methods=['GET'])
def calculate_price():
    return render_template('calculate_price.html')

@app.route('/recipes', methods=['GET'])
def view_recipes():
    recipes = Recipe.query.all()
    return render_template('recipes.html', recipes=recipes)

@app.route('/recipes/save', methods=['POST'])
def save_recipe():
    data = request.get_json()
    
    try:
        name = data.get('name')
        price = float(data.get('price'))
        
        # Validate data
        if not name or name.strip() == '':
            return jsonify({'error': 'Recipe name is required'}), 400
        
        if price <= 0:
            return jsonify({'error': 'Price must be greater than 0'}), 400
            
        # Create new recipe
        new_recipe = Recipe(
            name=name,
            price=price
        )
        
        db.session.add(new_recipe)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Recipe saved successfully', 'recipe': new_recipe.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/recipes/<int:id>/delete', methods=['POST'])
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    
    try:
        db.session.delete(recipe)
        db.session.commit()
        flash('Recipe deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting recipe: {str(e)}', 'danger')
        
    return redirect(url_for('view_recipes'))

# Kitchen Display System routes
@app.route('/waiter', methods=['GET'])
def waiter_interface():
    recipes = Recipe.query.all()
    return render_template('waiter.html', recipes=recipes)

@app.route('/chef', methods=['GET'])
def chef_interface():
    pending_orders = KitchenOrder.query.filter_by(status='pending').order_by(KitchenOrder.created_at).all()
    return render_template('chef.html', orders=pending_orders)

@app.route('/kitchen-orders', methods=['POST'])
def create_kitchen_order():
    data = request.get_json()
    
    try:
        # Create new order
        new_order = KitchenOrder(
            table_number=data['tableNumber'],
            special_notes=data.get('specialNotes', '')
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the order ID
        
        # Add items to the order
        for item in data['items']:
            order_item = KitchenOrderItem(
                order_id=new_order.id,
                recipe_id=item['recipeId'],
                quantity=item['quantity'],
                special_instructions=item.get('specialInstructions', '')
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order': new_order.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/kitchen-orders/<int:order_id>/status', methods=['PUT'])
def update_kitchen_order_status(order_id):
    order = KitchenOrder.query.get_or_404(order_id)
    data = request.get_json()
    
    try:
        order.status = data['status']
        
        # If marked as completed, set completed timestamp
        if order.status == 'completed':
            order.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/kitchen-orders/pending', methods=['GET'])
def get_pending_kitchen_orders_api():
    orders = KitchenOrder.query.filter_by(status='pending').order_by(KitchenOrder.created_at).all()
    return jsonify([order.to_dict() for order in orders])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)