import os
import re
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, template_folder="templates")
app.secret_key = "yoursecretkey"
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/shaheen_atier'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='cart_items')
    item = db.relationship('Item')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='wishlist_items')
    item = db.relationship('Item')

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    landmark = db.Column(db.String(100), nullable=True)
    address_type = db.Column(db.String(20), default='home')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='addresses')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='orders')
    address = db.relationship('Address')
    order_items = db.relationship('OrderItem', backref='order')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    item = db.relationship('Item')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_admin():
    if 'user' not in session:
        return False
    user = User.query.get(session['user']['id'])
    return user and user.is_admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Admin access required!', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login to continue.', 'error')
            return redirect(url_for('signIn'))
        return f(*args, **kwargs)
    return decorated_function

def add_sample_data():
    """Add sample products to database automatically"""
    print("Adding sample data to database...")
    
    sample_products = [
        # Popular Items
        {
            'title': 'Elegant Black Abaya',
            'price': '₹1,499',
            'image': 'images/img1.jpg',
            'section': 'Popular Items',
            'description': 'Classic black abaya with elegant embroidery and comfortable fit. Perfect for daily wear and special occasions.'
        },
        {
            'title': 'Embroidered Cream Abaya', 
            'price': '₹1,799',
            'image': 'images/img2.jpg',
            'section': 'Popular Items',
            'description': 'Beautiful cream colored abaya with intricate embroidery work. Made with premium quality fabric.'
        },
        {
            'title': 'Designer Navy Blue Abaya',
            'price': '₹2,199',
            'image': 'images/img3.jpeg',
            'section': 'Popular Items',
            'description': 'Latest designer navy blue abaya with modern cuts and patterns. Exclusive collection.'
        },
        {
            'title': 'Traditional Maroon Abaya',
            'price': '₹1,299',
            'image': 'images/img7.jpg',
            'section': 'Popular Items',
            'description': 'Traditional maroon abaya perfect for special occasions. Rich color and elegant design.'
        },
        
        # New Arrivals
        {
            'title': 'Casual Grey Abaya',
            'price': '₹999',
            'image': 'images/img5.jpg',
            'section': 'New Arrivals',
            'description': 'Comfortable casual grey abaya for everyday wear. Lightweight and easy to maintain.'
        },
        {
            'title': 'Luxury Golden Abaya',
            'price': '₹2,499',
            'image': 'images/img6.jpg',
            'section': 'New Arrivals',
            'description': 'Premium golden abaya with luxury fabric and design. Perfect for weddings and festivals.'
        },
        {
            'title': 'Simple White Abaya',
            'price': '₹1,199',
            'image': 'images/img7.jpg',
            'section': 'New Arrivals',
            'description': 'Simple and elegant white abaya for daily use. Pure cotton fabric for maximum comfort.'
        },
        {
            'title': 'Floral Print Abaya',
            'price': '₹1,899',
            'image': 'images/img8.jpg',
            'section': 'New Arrivals',
            'description': 'Beautiful floral print abaya with modern design. Unique pattern and excellent finish.'
        },
        
        # Best Deals
        {
            'title': 'Premium Silk Abaya',
            'price': '₹1,999',
            'image': 'images/img1.jpg',
            'section': 'Best Deals',
            'description': 'Premium silk abaya with exclusive design. Limited time offer with great discount.'
        },
        {
            'title': 'Casual Wear Abaya',
            'price': '₹899',
            'image': 'images/img2.jpg',
            'section': 'Best Deals',
            'description': 'Affordable casual wear abaya. Best value for money with premium look.'
        },
        {
            'title': 'Designer Collection Abaya',
            'price': '₹2,299',
            'image': 'images/img3.jpeg',
            'section': 'Best Deals',
            'description': 'Designer collection abaya at special price. High quality fabric with perfect stitching.'
        },
        {
            'title': 'Traditional Embroidered Abaya',
            'price': '₹1,599',
            'image': 'images/img7.jpg',
            'section': 'Best Deals',
            'description': 'Traditional embroidered abaya with handwork. Special discount for limited period.'
        }
    ]
    
    try:
        for product_data in sample_products:
            # Check if product already exists
            existing_product = Item.query.filter_by(title=product_data['title']).first()
            if not existing_product:
                product = Item(
                    title=product_data['title'],
                    price=product_data['price'],
                    image=product_data['image'],
                    section=product_data['section'],
                    description=product_data['description']
                )
                db.session.add(product)
        
        db.session.commit()
        print("Sample data added successfully!")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.session.rollback()

def init_db():
    with app.app_context():
        db.create_all()
        # Add sample data if database is empty
        if Item.query.count() == 0:
            add_sample_data()

# Routes
@app.route('/')
def home():
  
    sections = [  
        {
            "title": "Popular Items", 
            "cards": Item.query.filter_by(section="Popular Items").limit(6).all(),
            "total_count": Item.query.filter_by(section="Popular Items").count()
        },
        {
            "title": "New Arrivals", 
            "cards": Item.query.filter_by(section="New Arrivals").limit(6).all(),
            "total_count": Item.query.filter_by(section="New Arrivals").count()
        },
        {
            "title": "Best Deals", 
            "cards": Item.query.filter_by(section="Best Deals").limit(6).all(),
            "total_count": Item.query.filter_by(section="Best Deals").count()
        }
    ]

    empty_sections = all(len(section["cards"]) == 0 for section in sections)
    
    # Get cart count for logged in users
    cart_count = 0
    if 'user' in session:
        cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()

    return render_template('home.html', sections=sections, user=session.get('user'), 
                         empty_sections=empty_sections, cart_count=cart_count)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        items = Item.query.filter(Item.title.ilike(f'%{query}%') | Item.description.ilike(f'%{query}%')).all()
    else:
        items = []
    
    cart_count = 0
    if 'user' in session:
        cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('search.html', items=items, query=query, user=session.get('user'), cart_count=cart_count)

@app.route('/about')
def about():
    cart_count = 0
    if 'user' in session:
        cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    return render_template('about.html', user=session.get('user'), cart_count=cart_count)
    
@app.route('/collection')
def collection():
    filter_type = request.args.get('filter', '')
    
    if filter_type == 'popular':
        items = Item.query.filter_by(section="Popular Items").all()
        filter_title = "Popular Items"
    elif filter_type == 'new':
        items = Item.query.filter_by(section="New Arrivals").all()
        filter_title = "New Arrivals"
    elif filter_type == 'deals':
        items = Item.query.filter_by(section="Best Deals").all()
        filter_title = "Best Deals"
    else:
        items = Item.query.all()
        filter_title = "All Products"
    
    cart_count = 0
    if 'user' in session:
        cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('collection.html', items=items, user=session.get('user'), 
                         cart_count=cart_count, filter_title=filter_title)

@app.route('/contact')
def contact():
    cart_count = 0
    if 'user' in session:
        cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    return render_template('contact.html', user=session.get('user'), cart_count=cart_count)

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    if name and email and message:
        flash('Thank you for your message! We\'ll get back to you soon.', 'success')
    else:
        flash('Please fill all fields.', 'error')
    return redirect(url_for('contact'))

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_image = request.files.get('profile_image')
        
        if not all([name, email, password, confirm_password]):
            flash('Please fill all fields.', 'error')
            return redirect(url_for('register'))
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('register'))
        
        profile_image_path = None
        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            filename = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_image_path = f'images/{filename}'
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            profile_image=profile_image_path,
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('signIn'))
    
    return render_template('register.html', user=session.get('user'))

@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return redirect(url_for('signIn'))
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('signIn'))
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user and check_password_hash(user.password, password):
            session['user'] = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'profile_image': user.profile_image,
                'is_admin': user.is_admin
            }
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('signIn.html', user=session.get('user'))

@app.route('/signout')
def signout():
    session.pop('user', None)
    flash('You have been signed out successfully.', 'success')
    return redirect(url_for('home'))

# User Profile & Account Management
@app.route('/profile')
@login_required
def profile():
    user_data = User.query.get(session['user']['id'])
    addresses = Address.query.filter_by(user_id=session['user']['id']).all()
    cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    wishlist_count = Wishlist.query.filter_by(user_id=session['user']['id']).count()
    orders_count = Order.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('profile.html', user=user_data, addresses=addresses,
                         cart_count=cart_count, wishlist_count=wishlist_count, orders_count=orders_count)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user']['id'])
    name = request.form.get('name')
    profile_image = request.files.get('profile_image')
    
    if name:
        user.name = name
    
    if profile_image and allowed_file(profile_image.filename):
        filename = secure_filename(profile_image.filename)
        filename = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user.profile_image = f'images/{filename}'
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

# Address Management
@app.route('/address/add', methods=['POST'])
@login_required
def add_address():
    name = request.form.get('name')
    phone = request.form.get('phone')
    address_line1 = request.form.get('address_line1')
    address_line2 = request.form.get('address_line2')
    city = request.form.get('city')
    state = request.form.get('state')
    pincode = request.form.get('pincode')
    landmark = request.form.get('landmark')
    address_type = request.form.get('address_type', 'home')
    is_default = request.form.get('is_default') == 'on'
    
    if not all([name, phone, address_line1, city, state, pincode]):
        flash('Please fill all required fields.', 'error')
        return redirect(url_for('profile'))
    
    # If setting as default, remove default from other addresses
    if is_default:
        Address.query.filter_by(user_id=session['user']['id']).update({'is_default': False})
    
    new_address = Address(
        user_id=session['user']['id'],
        name=name,
        phone=phone,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        pincode=pincode,
        landmark=landmark,
        address_type=address_type,
        is_default=is_default
    )
    
    db.session.add(new_address)
    db.session.commit()
    flash('Address added successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/address/delete/<int:address_id>')
@login_required
def delete_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=session['user']['id']).first()
    if address:
        db.session.delete(address)
        db.session.commit()
        flash('Address deleted successfully!', 'success')
    return redirect(url_for('profile'))

# Cart Management
@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=session['user']['id']).all()
    total_amount = sum(float(cart.item.price.replace('₹', '').replace(',', '')) * cart.quantity for cart in cart_items)
    cart_count = len(cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount, 
                         user=session.get('user'), cart_count=cart_count)

@app.route('/cart/add/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found!'})
    
    # Check if item already in cart
    existing_cart_item = Cart.query.filter_by(user_id=session['user']['id'], item_id=item_id).first()
    if existing_cart_item:
        return jsonify({'success': False, 'message': 'Item already in cart!'})
    else:
        new_cart_item = Cart(user_id=session['user']['id'], item_id=item_id)
        db.session.add(new_cart_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Item added to cart!'})

@app.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.filter_by(id=cart_id, user_id=session['user']['id']).first()
    if cart_item:
        quantity = int(request.form.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            db.session.commit()
            flash('Cart updated!', 'success')
        else:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.filter_by(id=cart_id, user_id=session['user']['id']).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

# Wishlist Management
@app.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=session['user']['id']).all()
    cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('wishlist.html', wishlist_items=wishlist_items, 
                         user=session.get('user'), cart_count=cart_count)

@app.route('/wishlist/add/<int:item_id>')
@login_required
def add_to_wishlist(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found!'})
    
    # Check if item already in wishlist
    existing_wishlist_item = Wishlist.query.filter_by(user_id=session['user']['id'], item_id=item_id).first()
    if not existing_wishlist_item:
        new_wishlist_item = Wishlist(user_id=session['user']['id'], item_id=item_id)
        db.session.add(new_wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Item added to wishlist!'})
    else:
        return jsonify({'success': False, 'message': 'Item already in wishlist!'})

@app.route('/wishlist/remove/<int:wishlist_id>')
@login_required
def remove_from_wishlist(wishlist_id):
    wishlist_item = Wishlist.query.filter_by(id=wishlist_id, user_id=session['user']['id']).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Item removed from wishlist!', 'success')
    return redirect(url_for('wishlist'))

# Product Routes
@app.route('/product/<title>')
def product(title):
    item = Item.query.filter_by(title=title).first()
    if item:
        similar_items = Item.query.filter_by(section=item.section).filter(Item.id != item.id).limit(4).all()
        
        # Check if item is in user's wishlist
        in_wishlist = False
        if 'user' in session:
            in_wishlist = Wishlist.query.filter_by(user_id=session['user']['id'], item_id=item.id).first() is not None
        
        cart_count = 0
        if 'user' in session:
            cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
        
        return render_template('product.html', item=item, similar_items=similar_items, 
                             user=session.get('user'), in_wishlist=in_wishlist, cart_count=cart_count)
    return "Item not found", 404

# Checkout & Orders
@app.route('/checkout')
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=session['user']['id']).all()
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))
    
    addresses = Address.query.filter_by(user_id=session['user']['id']).all()
    total_amount = sum(float(cart.item.price.replace('₹', '').replace(',', '')) * cart.quantity for cart in cart_items)
    cart_count = len(cart_items)
    
    return render_template('checkout.html', cart_items=cart_items, addresses=addresses,
                         total_amount=total_amount, user=session.get('user'), cart_count=cart_count)

@app.route('/order/create', methods=['POST'])
@login_required
def create_order():
    address_id = request.form.get('address_id')
    if not address_id:
        flash('Please select a delivery address.', 'error')
        return redirect(url_for('checkout'))
    
    cart_items = Cart.query.filter_by(user_id=session['user']['id']).all()
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))
    
    # Calculate total amount
    total_amount = sum(float(cart.item.price.replace('₹', '').replace(',', '')) * cart.quantity for cart in cart_items)
    
    # Create order
    new_order = Order(
        user_id=session['user']['id'],
        address_id=address_id,
        total_amount=total_amount,
        status='confirmed',
        payment_status='paid'  # For demo purposes
    )
    
    db.session.add(new_order)
    db.session.flush()  # Get the order ID
    
    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            price=float(cart_item.item.price.replace('₹', '').replace(',', ''))
        )
        db.session.add(order_item)
    
    # Clear cart
    Cart.query.filter_by(user_id=session['user']['id']).delete()
    
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('order_confirmation', order_id=new_order.id))

@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session['user']['id']).first_or_404()
    cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('order_confirmation.html', order=order, user=session.get('user'), cart_count=cart_count)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=session['user']['id']).order_by(Order.created_at.desc()).all()
    cart_count = Cart.query.filter_by(user_id=session['user']['id']).count()
    
    return render_template('orders.html', orders=user_orders, user=session.get('user'), cart_count=cart_count)

# Admin Routes
@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    admin_exists = User.query.filter_by(is_admin=True).first()
    if admin_exists:
        flash('Admin account already exists!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        secret_key = request.form.get('secret_key')
        
        if not all([name, email, password, confirm_password, secret_key]):
            flash('Please fill all fields.', 'error')
            return redirect(url_for('create_admin'))
        
        if secret_key != "ADMIN_SETUP_2024":
            flash('Invalid secret key!', 'error')
            return redirect(url_for('create_admin'))
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('create_admin'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('create_admin'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('create_admin'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('create_admin'))
        
        hashed_password = generate_password_hash(password)
        admin_user = User(
            name=name,
            email=email,
            password=hashed_password,
            is_admin=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        flash('Admin account created successfully! Please sign in.', 'success')
        return redirect(url_for('signIn'))
    
    return render_template('create_admin.html', user=session.get('user'))

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Item.query.all()
    return render_template('admin_products.html', products=products, user=session.get('user'))

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Item.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.title = request.form.get('title')
        product.price = request.form.get('price')
        product.section = request.form.get('section')
        product.description = request.form.get('description')
        
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = f'images/{filename}'
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('edit_product.html', product=product, user=session.get('user'))

@app.route('/admin/product/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = Item.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/add_item', methods=['GET', 'POST'])
@admin_required
def add_item():
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        section = request.form.get('section')
        description = request.form.get('description')
        file = request.files.get('image')

        print(f"DEBUG: Adding item - Title: {title}, Section: {section}")  # Debug line

        if title and price and section and description and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_item = Item(title=title, price=price, image=f'images/{filename}', section=section, description=description)
            db.session.add(new_item)
            db.session.commit()

            print(f"DEBUG: Item added successfully - ID: {new_item.id}")  # Debug line

            flash('Item added successfully!', 'success')
            return redirect(url_for('add_item'))
        else:
            flash('Please fill all fields and upload a valid image.', 'error')
    return render_template('add_item.html', user=session.get('user'))







if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True)