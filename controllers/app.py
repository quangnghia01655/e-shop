from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import logging
from functools import wraps
from math import ceil
import sys

# Thêm đường dẫn models vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../models')))
from models import db, User, Seller, Category, Product, Cart, CartItem, Order, OrderItem, Notification

app = Flask(
    __name__,
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../views')),
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../static'))
)
app.config['SECRET_KEY'] = 'your-secret-key'

# Ensure instance folder exists before DB init (for SQLite on Render)
instance_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance'))
os.makedirs(instance_folder, exist_ok=True)

db_path = os.path.join(instance_folder, 'ecommerce.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)
app.logger.addHandler(file_handler)

# Hàm hỗ trợ
def get_cart_item_count(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return 0
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    return sum(item.quantity for item in cart_items)

def get_notification_count(user_id):
    # Đếm số thông báo thực tế trong database
    return Notification.query.filter_by(user_id=user_id).count()

# Decorator kiểm tra đăng nhập
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vui lòng đăng nhập để tiếp tục', 'error')
                return redirect(url_for('login', next=request.url))
            user = db.session.get(User, session['user_id'])
            if not user:
                session.clear()
                flash('Người dùng không tồn tại', 'error')
                return redirect(url_for('login', next=request.url))
            if role == 'seller' and not user.is_seller:
                flash('Bạn không có quyền truy cập trang này', 'error')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def create_notification(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()

# Routes
@app.route('/')
def index():
    try:
        categories = Category.query.all()
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 12
        q = request.args.get('q', '').strip()
        if category_id:
            products_query = Product.query.filter_by(category_id=category_id)
        else:
            products_query = Product.query
        if q:
            products_query = products_query.filter(Product.name.ilike(f'%{q}%'))
        total_products = products_query.count()
        products = products_query.offset((page-1)*per_page).limit(per_page).all()
        total_pages = ceil(total_products / per_page) if total_products else 1
        # Lấy sản phẩm bán chạy nhất (carousel)
        best_sellers = []
        try:
            # Sử dụng biến all_products để tránh ghi đè biến products đã phân trang
            all_products = Product.query.all()
            best_sellers = []
            if all_products:
                purchased_list = [p.total_purchased for p in all_products]
                max_purchased = max(purchased_list)
                min_purchased = min(purchased_list)
                import random
                if max_purchased == min_purchased:
                    # Nếu tất cả sản phẩm có số lượng mua bằng nhau (kể cả 0), lấy random 12 sản phẩm
                    best_sellers = random.sample(all_products, min(12, len(all_products)))
                else:
                    # Sắp xếp giảm dần theo số lượng mua
                    sorted_products = sorted(all_products, key=lambda p: p.total_purchased, reverse=True)
                    ranked = [p for p in sorted_products if p.total_purchased > min_purchased]
                    if len(ranked) < 12:
                        others = [p for p in all_products if p not in ranked]
                        random.shuffle(others)
                        best_sellers = ranked + others[:12-len(ranked)]
                    else:
                        best_sellers = ranked[:12]
            # Nếu vẫn không có sản phẩm nào (all_products rỗng hoặc best_sellers rỗng), lấy random tối đa 12 sản phẩm bất kỳ
            if not best_sellers and all_products:
                import random
                best_sellers = random.sample(all_products, min(12, len(all_products)))
            best_sellers = [p.to_dict() for p in best_sellers]
        except Exception as e:
            app.logger.warning(f'Lỗi lấy sản phẩm bán chạy: {e}')
            best_sellers = []
        is_seller = False
        cart_count = 0
        notification_count = 0
        user = None
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                is_seller = user.is_seller
                cart_count = get_cart_item_count(user.id)
                notification_count = get_notification_count(user.id)
        app.logger.info(f'Truy cập trang chủ, user_id: {session.get("user_id", "không đăng nhập")}, sản phẩm: {len(products)}')
        return render_template('index.html', categories=categories, products=products, 
                             is_seller=is_seller, cart_count=cart_count, 
                             notification_count=notification_count, user=user, best_sellers=best_sellers,
                             page=page, total_pages=total_pages, category_id=category_id, q=q)
    except Exception as e:
        app.logger.error(f'Lỗi trong route index: {str(e)}')
        flash(f'Lỗi: {str(e)}', 'error')
        return render_template('index.html', categories=[], products=[], 
                             is_seller=False, cart_count=0, notification_count=0, user=None, best_sellers=[],
                             page=1, total_pages=1, category_id=None, q='')

@app.route('/profile')
@login_required()
def profile():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route profile')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    seller = Seller.query.filter_by(user_id=user.id).first()
    orders = Order.query.filter_by(user_id=user.id).all()
    pending_orders = [order for order in orders if order.status == 'pending']
    app.logger.info(f'Truy cập hồ sơ, user_id: {user.id}, đơn hàng: {len(orders)}')
    return render_template('profile.html', user=user, seller=seller, 
                         orders=orders, pending_orders=pending_orders,
                         cart_count=cart_count, notification_count=notification_count)

@app.route('/settings', methods=['POST'])
def settings():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route settings')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        if not name or not email:
            app.logger.warning(f'Thiếu thông tin họ tên hoặc email cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Họ tên và email không được để trống'})
        if name:
            user.name = name
        if email and email != user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                app.logger.warning(f'Email {email} đã được sử dụng')
                return jsonify({'status': 'error', 'message': 'Email đã được sử dụng'})
            user.email = email
        if password:
            user.password = generate_password_hash(password, method='sha256')
        db.session.commit()
        app.logger.info(f'Cập nhật thông tin thành công cho user_id: {user.id}')
        return jsonify({'status': 'success', 'message': 'Cập nhật thông tin thành công'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Lỗi trong route settings: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Lỗi khi cập nhật: {str(e)}'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    cart_count = get_cart_item_count(session.get('user_id', 0))
    notification_count = get_notification_count(session.get('user_id', 0))
    user = db.session.get(User, session.get('user_id')) if 'user_id' in session else None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not name or not email or not password:
            app.logger.warning('Thiếu thông tin đăng ký')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin'})
        if '@' not in email:
            app.logger.warning('Email không hợp lệ khi đăng ký')
            return jsonify({'status': 'error', 'message': 'Email không hợp lệ'})
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
            app.logger.info(f'Đăng ký thành công cho email: {email}')
            return jsonify({'status': 'success', 'message': 'Đăng ký thành công! Vui lòng đăng nhập.', 'redirect': url_for('login')})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Lỗi trong route register: {str(e)}')
            return jsonify({'status': 'error', 'message': 'Email đã tồn tại'})
    app.logger.info('Truy cập trang đăng ký')
    return render_template('register.html', cart_count=cart_count, 
                         notification_count=notification_count, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    cart_count = get_cart_item_count(session.get('user_id', 0))
    notification_count = get_notification_count(session.get('user_id', 0))
    user = db.session.get(User, session.get('user_id')) if 'user_id' in session else None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            app.logger.warning('Thiếu email hoặc mật khẩu khi đăng nhập')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ email và mật khẩu'})
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            app.logger.info(f'Đăng nhập thành công cho user_id: {user.id}')
            return jsonify({'status': 'success', 'message': 'Đăng nhập thành công!', 'redirect': url_for('index')})
        app.logger.warning(f'Đăng nhập thất bại cho email: {email}')
        return jsonify({'status': 'error', 'message': 'Thông tin đăng nhập không đúng', 'email': email})
    app.logger.info('Truy cập trang đăng nhập')
    return render_template('login.html', cart_count=cart_count, 
                         notification_count=notification_count, user=user)

@app.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id', 'không đăng nhập')
    app.logger.info(f'Logout attempt for user_id: {user_id}')
    try:
        session.clear()
        app.logger.info(f'Session cleared successfully for user_id: {user_id}')
        flash('Đã đăng xuất thành công', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        app.logger.error(f'Error during logout for user_id: {user_id}: {str(e)}')
        flash('Lỗi khi đăng xuất', 'error')
        return redirect(url_for('index'))

@app.route('/register_seller', methods=['GET', 'POST'])
@login_required()
def register_seller():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route register_seller')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    if request.method == 'POST':
        # Lấy name và email từ form, nếu không có thì lấy từ user
        name = request.form.get('name') or user.name
        email = request.form.get('email') or user.email
        phone = request.form.get('phone')
        shop_name = request.form.get('shop_name')
        password = request.form.get('password')
        if not all([name, email, phone, shop_name, password]):
            app.logger.warning(f'Thiếu thông tin đăng ký người bán cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin'})
        if not check_password_hash(user.password, password):
            app.logger.warning(f'Mật khẩu không đúng cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Mật khẩu không đúng'})
        new_seller = Seller(user_id=user.id, shop_name=shop_name, phone=phone)
        user.is_seller = True
        db.session.add(new_seller)
        db.session.commit()
        app.logger.info(f'Đăng ký người bán thành công cho user_id: {user.id}, shop_name: {shop_name}')
        return jsonify({'status': 'success', 'message': 'Đăng ký trở thành người bán thành công!', 'redirect': url_for('index')})
    app.logger.info(f'Truy cập trang đăng ký người bán, user_id: {user.id}')
    return render_template('register_seller.html', cart_count=cart_count, 
                         notification_count=notification_count, user=user)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route add_to_cart')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    product = db.session.get(Product, product_id)
    if not product:
        app.logger.error(f'Không tìm thấy sản phẩm với product_id: {product_id}')
        return jsonify({'status': 'error', 'message': 'Sản phẩm không tồn tại'})
    quantity = request.form.get('quantity', type=int, default=1)
    if quantity < 1:
        app.logger.warning(f'Số lượng không hợp lệ: {quantity} cho product_id: {product_id}')
        return jsonify({'status': 'error', 'message': 'Số lượng không hợp lệ'})
    cart = Cart.query.filter_by(user_id=session['user_id']).first()
    if not cart:
        cart = Cart(user_id=session['user_id'])
        db.session.add(cart)
        db.session.commit()
        app.logger.info(f'Tạo giỏ hàng mới cho user_id: {session["user_id"]}')
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
        app.logger.info(f'Cập nhật số lượng cho cart_item: {cart_item.id}, số lượng mới: {cart_item.quantity}')
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
        app.logger.info(f'Thêm cart_item mới cho product_id: {product_id}, số lượng: {quantity}')
    db.session.commit()
    cart_count = get_cart_item_count(session['user_id'])
    create_notification(session['user_id'], f"Bạn đã thêm sản phẩm '{product.name}' vào giỏ hàng.")
    app.logger.info(f'Thêm sản phẩm vào giỏ hàng thành công, user_id: {session["user_id"]}, cart_count: {cart_count}')
    return jsonify({'status': 'success', 'message': 'Sản phẩm đã được thêm vào giỏ hàng!', 'cart_count': cart_count})

@app.route('/update_cart/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route update_cart')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    cart_item = db.session.get(CartItem, cart_id)
    if not cart_item:
        app.logger.error(f'Không tìm thấy cart_item với id: {cart_id}')
        return jsonify({'status': 'error', 'message': 'Mục giỏ hàng không tồn tại'})
    if cart_item.cart.user_id != session['user_id']:
        app.logger.error(f'Không có quyền truy cập cart_item: {cart_id} cho user_id: {session["user_id"]}')
        return jsonify({'status': 'error', 'message': 'Không có quyền cập nhật mục này'})
    quantity = request.form.get('quantity', type=int)
    if quantity is None or quantity < 1:
        app.logger.warning(f'Số lượng không hợp lệ: {quantity} cho cart_item: {cart_id}')
        return jsonify({'status': 'error', 'message': 'Số lượng không hợp lệ'})
    cart_item.quantity = quantity
    db.session.commit()
    cart = Cart.query.filter_by(user_id=session['user_id']).first()
    total = 0
    if cart:
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        for item in cart_items:
            product = db.session.get(Product, item.product_id)
            if product:
                total += product.price * item.quantity
            else:
                app.logger.warning(f'Không tìm thấy sản phẩm với product_id: {item.product_id} cho cart_item: {item.id}')
    app.logger.info(f'Cập nhật cart_item: {cart_id}, số lượng mới: {quantity}, tổng tiền: {total}')
    return jsonify({'status': 'success', 'message': 'Cập nhật giỏ hàng thành công', 'cart_count': get_cart_item_count(session['user_id']), 'total': total})

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    app.logger.info(f'Nhận yêu cầu xóa cart_item: {cart_item_id}')
    
    # Check if the request is AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        app.logger.warning(f'Yêu cầu không phải AJAX cho cart_item: {cart_item_id}')
        return jsonify({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}), 400

    # Check if user is logged in
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route remove_from_cart')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'}), 401

    # Verify user exists
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'}), 401

    # Verify cart item exists
    cart_item = db.session.get(CartItem, cart_item_id)
    if not cart_item:
        app.logger.error(f'Không tìm thấy cart_item với id: {cart_item_id}')
        return jsonify({'status': 'error', 'message': 'Mục giỏ hàng không tồn tại'}), 404

    # Verify cart item belongs to the user
    if cart_item.cart.user_id != session['user_id']:
        app.logger.error(f'Không có quyền truy cập cart_item: {cart_item_id} cho user_id: {session["user_id"]}')
        return jsonify({'status': 'error', 'message': 'Không có quyền xóa mục này'}), 403

    try:
        # Store product details for logging
        product_id = cart_item.product_id
        quantity = cart_item.quantity

        # Delete the cart item
        db.session.delete(cart_item)
        db.session.commit()

        # Update notification count
        session['notification_count'] = session.get('notification_count', 0) + 1
        create_notification(session['user_id'], f"Bạn đã xóa sản phẩm khỏi giỏ hàng.")

        # Calculate new cart total
        cart = Cart.query.filter_by(user_id=session['user_id']).first()
        total = 0
        cart_count = 0
        if cart:
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
            cart_count = sum(item.quantity for item in cart_items)
            for item in cart_items:
                product = db.session.get(Product, item.product_id)
                if product:
                    total += product.price * item.quantity
                else:
                    app.logger.warning(f'Không tìm thấy sản phẩm với product_id: {item.product_id} cho cart_item: {item.id}')

        app.logger.info(f'Xóa cart_item: {cart_item_id}, product_id: {product_id}, số lượng: {quantity}, user_id: {session["user_id"]}, tổng tiền còn lại: {total}')
        return jsonify({
            'status': 'success',
            'message': 'Đã xóa sản phẩm khỏi giỏ hàng',
            'cart_count': cart_count,
            'total': total
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Lỗi khi xóa cart_item: {cart_item_id}, lỗi: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Lỗi khi xóa sản phẩm: {str(e)}'}), 500

@app.route('/cart')
@login_required()
def cart():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route cart')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        app.logger.info(f'Không tìm thấy giỏ hàng cho user_id: {user.id}')
        return render_template('cart.html', products=[], total=0, cart_count=cart_count, 
                             notification_count=notification_count, user=user)
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    products = []
    total = 0
    for item in cart_items:
        product = db.session.get(Product, item.product_id)
        if product:
            products.append({'id': item.id, 'product': product, 'quantity': item.quantity})
            total += product.price * item.quantity
        else:
            app.logger.warning(f'Không tìm thấy sản phẩm với product_id: {item.product_id} cho cart_item: {item.id}')
    app.logger.info(f'Tải giỏ hàng cho user_id: {user.id}, số lượng sản phẩm: {len(products)}, tổng tiền: {total}')
    return render_template('cart.html', products=products, total=total, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required()
def checkout():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route checkout')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        app.logger.info(f'Không tìm thấy giỏ hàng cho user_id: {user.id}')
        return jsonify({'status': 'error', 'message': 'Giỏ hàng trống'})
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        app.logger.info(f'Giỏ hàng trống cho user_id: {user.id}')
        return jsonify({'status': 'error', 'message': 'Giỏ hàng trống'})
    if request.method == 'POST':
        name = request.form.get('name')
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')
        if not all([name, shipping_address, payment_method]):
            app.logger.warning(f'Thiếu thông tin thanh toán cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin'})
        total = sum(db.session.get(Product, item.product_id).price * item.quantity for item in cart_items if db.session.get(Product, item.product_id))
        order = Order(user_id=user.id, total_amount=total, status='pending', 
                      payment_method=payment_method, shipping_address=shipping_address)
        db.session.add(order)
        db.session.commit()
        for item in cart_items:
            product = db.session.get(Product, item.product_id)
            if product:
                order_item = OrderItem(order_id=order.id, product_id=product.id, 
                                      quantity=item.quantity, price=product.price)
                db.session.add(order_item)
                db.session.delete(item)
        db.session.commit()
        app.logger.info(f'Tạo đơn hàng thành công cho user_id: {user.id}, order_id: {order.id}, tổng tiền: {total}')
        return jsonify({'status': 'success', 'message': 'Đặt hàng thành công!'})
    products = [{'product': db.session.get(Product, item.product_id), 'quantity': item.quantity} for item in cart_items]
    products = [p for p in products if p['product']]
    total = sum(product['product'].price * product['quantity'] for product in products)
    app.logger.info(f'Truy cập trang thanh toán, user_id: {user.id}, tổng tiền: {total}')
    return render_template('checkout.html', products=products, total=total, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required(role='seller')
def add_product():
    if 'user_id' not in session or not db.session.get(User, session['user_id']).is_seller:
        app.logger.error('Không có quyền truy cập route add_product')
        return jsonify({'status': 'error', 'message': 'Yêu cầu quyền người bán'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        category_id = request.form.get('category_id', type=int)
        if not all([name, price, category_id]):
            app.logger.warning(f'Thiếu thông tin bắt buộc cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin bắt buộc'})
        if price <= 0:
            app.logger.warning(f'Giá không hợp lệ: {price} cho user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Giá sản phẩm phải lớn hơn 0'})
        category = db.session.get(Category, category_id)
        if not category:
            app.logger.error(f'Không tìm thấy danh mục với category_id: {category_id}')
            return jsonify({'status': 'error', 'message': 'Danh mục không tồn tại'})
        seller = Seller.query.filter_by(user_id=user.id).first()
        if not seller:
            app.logger.error(f'Không tìm thấy người bán với user_id: {user.id}')
            return jsonify({'status': 'error', 'message': 'Người bán không tồn tại'})
        new_product = Product(name=name, price=price, description=description, 
                             image_url=image_url, category_id=category_id, seller_id=seller.id)
        db.session.add(new_product)
        db.session.commit()
        create_notification(user.id, f"Bạn đã thêm sản phẩm mới: {name}.")
        app.logger.info(f'Thêm sản phẩm thành công: {name}, seller_id: {seller.id}')
        return jsonify({'status': 'success', 'message': 'Thêm sản phẩm thành công', 'redirect': url_for('seller_dashboard') + '?success=true&action=add'})
    categories = Category.query.all()
    app.logger.info(f'Truy cập trang thêm sản phẩm, user_id: {user.id}')
    return render_template('add_product.html', categories=categories, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/seller_dashboard')
@login_required()
def seller_dashboard():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route seller_dashboard')
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return redirect(url_for('login'))
    if not (user.is_seller or user.is_admin):
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('index'))
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    seller = Seller.query.filter_by(user_id=user.id).first()
    # Nếu là admin thì xem tất cả sản phẩm, nếu là seller thì chỉ xem sản phẩm của mình
    if user.is_admin:
        products = Product.query.all()
    elif seller:
        products = Product.query.filter_by(seller_id=seller.id).all()
    else:
        products = []
    app.logger.info(f'Truy cập bảng điều khiển người bán, user_id: {user.id}, sản phẩm: {len(products)}')
    return render_template('seller_dashboard.html', products=products, 
                         cart_count=cart_count, notification_count=notification_count, user=user, seller=seller)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required(role='seller')
def edit_product(product_id):
    if 'user_id' not in session or not db.session.get(User, session['user_id']).is_seller:
        app.logger.error('Không có quyền truy cập route edit_product')
        return jsonify({'status': 'error', 'message': 'Yêu cầu quyền người bán'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    product = db.session.get(Product, product_id)
    if not product:
        app.logger.error(f'Không tìm thấy sản phẩm với product_id: {product_id}')
        return jsonify({'status': 'error', 'message': 'Sản phẩm không tồn tại'})
    seller = Seller.query.filter_by(user_id=user.id).first()
    if not seller or product.seller_id != seller.id:
        app.logger.error(f'Không có quyền truy cập product_id: {product_id} bởi user_id: {user.id}')
        return jsonify({'status': 'error', 'message': 'Không có quyền sửa sản phẩm này'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        category_id = request.form.get('category_id', type=int)
        if not all([name, price, category_id]):
            app.logger.warning(f'Thiếu thông tin bắt buộc cho product_id: {product_id}')
            return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin bắt buộc'})
        if price <= 0:
            app.logger.warning(f'Giá không hợp lệ: {price} cho product_id: {product_id}')
            return jsonify({'status': 'error', 'message': 'Giá sản phẩm phải lớn hơn 0'})
        category = db.session.get(Category, category_id)
        if not category:
            app.logger.error(f'Không tìm thấy danh mục với category_id: {category_id}')
            return jsonify({'status': 'error', 'message': 'Danh mục không tồn tại'})
        product.name = name
        product.price = price
        product.description = description
        product.image_url = image_url
        product.category_id = category_id
        db.session.commit()
        create_notification(user.id, f"Bạn đã cập nhật sản phẩm: {name}.")
        app.logger.info(f'Cập nhật sản phẩm thành công: product_id: {product_id}')
        return jsonify({'status': 'success', 'message': 'Cập nhật sản phẩm thành công', 'redirect': url_for('seller_dashboard') + '?success=true&action=edit'})
    categories = Category.query.all()
    app.logger.info(f'Truy cập trang sửa sản phẩm, product_id: {product_id}, user_id: {user.id}')
    return render_template('edit_product.html', product=product, categories=categories, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required(role='seller')
def delete_product(product_id):
    if 'user_id' not in session or not db.session.get(User, session['user_id']).is_seller:
        app.logger.error('Không có quyền truy cập route delete_product')
        return jsonify({'status': 'error', 'message': 'Yêu cầu quyền người bán'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    product = db.session.get(Product, product_id)
    if not product:
        app.logger.error(f'Không tìm thấy sản phẩm với product_id: {product_id}')
        return jsonify({'status': 'error', 'message': 'Sản phẩm không tồn tại'})
    seller = Seller.query.filter_by(user_id=user.id).first()
    if not seller or product.seller_id != seller.id:
        app.logger.error(f'Không có quyền truy cập product_id: {product_id} bởi user_id: {user.id}')
        return jsonify({'status': 'error', 'message': 'Không có quyền xóa sản phẩm này'})
    db.session.delete(product)
    db.session.commit()
    create_notification(user.id, f"Bạn đã xóa sản phẩm: {product.name}.")
    app.logger.info(f'Xóa sản phẩm thành công: product_id: {product_id}')
    return jsonify({'status': 'success', 'message': 'Đã xóa sản phẩm thành công', 'redirect': url_for('seller_dashboard') + '?success=true&action=delete'})

@app.route('/orders')
@login_required()
def orders():
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route orders')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    orders = Order.query.filter_by(user_id=user.id).all()
    app.logger.info(f'Truy cập trang đơn hàng, user_id: {user.id}, số đơn hàng: {len(orders)}')
    return render_template('orders.html', orders=orders, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/order_details/<int:order_id>')
@login_required()
def order_details(order_id):
    if 'user_id' not in session:
        app.logger.error('Không có user_id trong session cho route order_details')
        return jsonify({'status': 'error', 'message': 'Vui lòng đăng nhập trước'})
    user = db.session.get(User, session['user_id'])
    if not user:
        app.logger.error(f'Không tìm thấy người dùng với user_id: {session["user_id"]}')
        session.clear()
        return jsonify({'status': 'error', 'message': 'Người dùng không tồn tại'})
    order = db.session.get(Order, order_id)
    if not order or order.user_id != user.id:
        app.logger.error(f'Không có quyền truy cập order_id: {order_id} bởi user_id: {user.id}')
        return jsonify({'status': 'error', 'message': 'Không có quyền xem đơn hàng này'})
    cart_count = get_cart_item_count(user.id)
    notification_count = get_notification_count(user.id)
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    app.logger.info(f'Truy cập chi tiết đơn hàng, order_id: {order_id}, user_id: {user.id}, số mục: {len(order_items)}')
    return render_template('order_details.html', order=order, order_items=order_items, 
                         cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/api/notifications')
@login_required()
def get_notifications():
    notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    data = [
        {
            'id': n.id,
            'message': n.message,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': n.is_read
        }
        for n in notifications
    ]
    return jsonify({'status': 'success', 'notifications': data})

@app.route('/api/notifications/clear', methods=['POST'])
@login_required()
def clear_notifications():
    Notification.query.filter_by(user_id=session['user_id']).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Đã xóa tất cả thông báo'})

@app.route('/debug')
def debug():
    try:
        category_count = db.session.execute(db.text("SELECT COUNT(*) FROM categories")).scalar()
        product_count = db.session.execute(db.text("SELECT COUNT(*) FROM products")).scalar()
        seller_count = db.session.execute(db.text("SELECT COUNT(*) FROM sellers")).scalar()
        user_count = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar()
        products = db.session.execute(db.text("SELECT id, name, category_id, seller_id FROM products LIMIT 5")).fetchall()
        app.logger.info(f'Truy cập route debug, danh mục: {category_count}, sản phẩm: {product_count}')
        return jsonify({
            "category_count": category_count,
            "product_count": product_count,
            "seller_count": seller_count,
            "user_count": user_count,
            "sample_products": [{"id": p.id, "name": p.name, "category_id": p.category_id, "seller_id": p.seller_id} for p in products]
        })
    except Exception as e:
        app.logger.error(f'Lỗi trong route debug: {str(e)}')
        return jsonify({"error": str(e)})

@app.route('/about')
def about():
    cart_count = get_cart_item_count(session.get('user_id', 0))
    notification_count = get_notification_count(session.get('user_id', 0))
    user = db.session.get(User, session.get('user_id')) if 'user_id' in session else None
    return render_template('about.html', cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    cart_count = get_cart_item_count(session.get('user_id', 0))
    notification_count = get_notification_count(session.get('user_id', 0))
    user = db.session.get(User, session.get('user_id')) if 'user_id' in session else None
    return render_template('product_detail.html', product=product, cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/admin/users')
@login_required(role='admin')
def admin_users():
    cart_count = get_cart_item_count(session.get('user_id', 0))
    notification_count = get_notification_count(session.get('user_id', 0))
    user = db.session.get(User, session.get('user_id')) if 'user_id' in session else None
    # Dữ liệu user sẽ được render động phía client hoặc truyền từ backend nếu cần
    return render_template('admin_users.html', cart_count=cart_count, notification_count=notification_count, user=user)

@app.route('/admin/api/users', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_api_users():
    if request.method == 'GET':
        users = User.query.all()
        user_list = []
        for u in users:
            user_list.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'is_seller': bool(u.is_seller),
                'is_admin': bool(u.is_admin)
            })
        return jsonify({'status': 'success', 'users': user_list})
    # Thêm mới user
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not all([name, email, password, role]):
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập đủ thông tin'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': 'Email đã tồn tại'}), 400
    is_seller = 1 if role == 'seller' else 0
    is_admin = 1 if role == 'admin' else 0
    hashed_password = generate_password_hash(password, method='sha256')
    user = User(name=name, email=email, password=hashed_password, is_seller=is_seller, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    create_notification(user.id, "Tài khoản của bạn đã được tạo bởi quản trị viên.")
    return jsonify({'status': 'success', 'message': 'Đã thêm người dùng thành công'})

@app.route('/admin/api/users/<int:user_id>', methods=['POST', 'DELETE'])
@login_required(role='admin')
def admin_api_user_update(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        create_notification(user.id, "Tài khoản của bạn đã bị xóa bởi quản trị viên.")
        return jsonify({'status': 'success', 'message': 'Đã xóa người dùng'})
    # Cập nhật user
    data = request.json
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    role = data.get('role')
    if role:
        user.is_seller = 1 if role == 'seller' else 0
        user.is_admin = 1 if role == 'admin' else 0
    password = data.get('password')
    if password:
        user.password = generate_password_hash(password, method='sha256')
    db.session.commit()
    create_notification(user.id, "Tài khoản của bạn đã được cập nhật bởi quản trị viên.")
    return jsonify({'status': 'success', 'message': 'Đã cập nhật người dùng'})

# Tạo cơ sở dữ liệu
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.logger.info('Khởi động ứng dụng Flask')
    app.run(debug=True)
