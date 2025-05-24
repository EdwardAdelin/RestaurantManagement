from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for flash messages
db = SQLAlchemy(app)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)