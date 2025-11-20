from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # Dùng cho User Management
from werkzeug.utils import secure_filename # Dùng cho File Upload

# --- Cấu hình và Khởi tạo Ứng dụng ---
app = Flask(__name__)
# Thiết lập khóa bí mật (Bắt buộc cho Flask)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key') 

# Cấu hình SQLite (Database Service)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cấu hình Upload File
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục upload nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

db = SQLAlchemy(app)

# --- Định nghĩa Mô hình (Models) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    files = db.relationship('File', backref='uploader', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Liên kết user
    
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False) # Đường dẫn tương đối
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Khởi tạo Login Manager và User Loader (User Management) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Hàm kiểm tra File hợp lệ ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Tạo DB (Chạy 1 lần) ---
with app.app_context():
    db.create_all() 

# =================================================================
#                         WEB INTERFACE ROUTES
# =================================================================

# --- 1. Trang Chủ ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 2. Đăng Ký (User Management, Thông báo thay thế Email) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Tên người dùng đã tồn tại!")

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password, email=email)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Thông báo (thay thế Email Notification - hiển thị trong Console)
        print(f"--- THÔNG BÁO HỆ THỐNG: User mới đã đăng ký: {username} ---")

        return redirect(url_for('login'))
    return render_template('register.html')

# --- 3. Đăng Nhập (User Management) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard')) 
        else:
            return render_template('login.html', error="Tên người dùng hoặc mật khẩu không đúng.")
    return render_template('login.html')

# --- 4. Đăng Xuất ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- 5. Dashboard (Dashboard: Hiển thị thống kê và Bài viết) ---
@app.route('/dashboard')
@login_required
def dashboard():
    total_users = User.query.count()
    total_files = File.query.count()
    total_posts = Post.query.count() 
    
    # Lấy 5 files mới nhất của người dùng hiện tại
    user_files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).limit(5).all()
    
    # Lấy TẤT CẢ bài viết của người dùng hiện tại, bao gồm cả đối tượng Author
    user_posts = Post.query.filter_by(user_id=current_user.id).join(User).all()
    
    context = {
        'total_users': total_users,
        'total_files': total_files,
        'total_posts': total_posts,
        'user_files': user_files,
        'user_posts': user_posts, # <--- ĐÃ THÊM BIẾN NÀY
    }
    return render_template('dashboard.html', **context)

# --- 6. Upload File (File Upload) ---
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', error="Không có phần file")
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('upload.html', error="Chưa chọn file")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(file_path)
            
            db_path = os.path.join('uploads', filename) 
            new_file = File(filename=filename, path=db_path, user_id=current_user.id)
            db.session.add(new_file)
            db.session.commit()
            
            return redirect(url_for('dashboard')) 
        else:
            return render_template('upload.html', error="Định dạng file không được phép.")
    return render_template('upload.html')

# =================================================================
#                       API ENDPOINT (CRUD)
# =================================================================

# --- 7. API Posts (GET/POST) ---
@app.route('/api/posts', methods=['GET', 'POST'])
@login_required
def api_posts():
    # GET: Lấy danh sách bài viết
    if request.method == 'GET':
        posts = Post.query.all()
        posts_list = [{'id': p.id, 'title': p.title, 'content': p.content, 'user_id': p.user_id} for p in posts]
        return jsonify(posts_list)

    # POST: Tạo bài viết mới
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'message': 'Thiếu dữ liệu Title hoặc Content'}), 400

        new_post = Post(title=data['title'], content=data['content'], user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return jsonify({'message': 'Bài viết đã được tạo', 'post_id': new_post.id}), 201

# --- 8. API Post Chi tiết (GET/PUT/DELETE) ---
@app.route('/api/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Kiểm tra quyền sở hữu
    if post.user_id != current_user.id:
        return jsonify({'message': 'Không có quyền truy cập'}), 403

    if request.method == 'GET':
        return jsonify({'id': post.id, 'title': post.title, 'content': post.content, 'user_id': post.user_id})

    elif request.method == 'PUT':
        data = request.get_json()
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        db.session.commit()
        return jsonify({'message': 'Bài viết đã được cập nhật'})

    elif request.method == 'DELETE':
        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': 'Bài viết đã được xóa'})
# --- Route Thêm Bài Viết Mới (CRUD Operation: Create) ---
@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            return render_template('create_post.html', error="Tiêu đề và Nội dung không được để trống.")
        
        # Tạo đối tượng Post mới
        post = Post(title=title, content=content, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        
        return redirect(url_for('dashboard')) # Sau khi tạo, chuyển hướng về Dashboard
        
    return render_template('create_post.html')
# --- 9. Route Xem Chi Tiết Bài Viết (CRUD Operation: Read) ---
@app.route('/post/<int:post_id>')
def view_post(post_id):
    # Dùng get_or_404 để tự động trả về lỗi 404 nếu không tìm thấy ID
    post = Post.query.get_or_404(post_id)
    
    # Lấy thông tin tác giả
    author = User.query.get(post.user_id)
    
    context = {
        'post': post,
        'author': author
    }
    return render_template('view_post.html', **context)

# --- Chạy Ứng dụng ---
if __name__ == '__main__':
    app.run(debug=True)