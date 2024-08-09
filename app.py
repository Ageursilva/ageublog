from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'd219b88288751e5a9a896e4db3e1500b' 
db = SQLAlchemy(app)

# Definição do modelo User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Definição do modelo Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Decorator para proteger rotas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def extract_image_and_excerpt(content):
    soup = BeautifulSoup(content, 'html.parser')
    image = soup.find('img')
    excerpt = soup.get_text()[:300]  # Exibir as primeiras 300 caracteres do texto
    return image['src'] if image else None, excerpt

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts_with_images_and_excerpts = []
    for post in pagination.items:
        image_url, excerpt = extract_image_and_excerpt(post.content)
        posts_with_images_and_excerpts.append({
            'post': post,
            'image_url': image_url,
            'excerpt': excerpt
        })
    return render_template('index.html', posts=posts_with_images_and_excerpts, pagination=pagination)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('admin'))
        else:
            flash('Nome de usuário ou senha incorretos')
    return render_template('login.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/admin', methods=['GET', 'POST'])
@login_required  # Protege a rota com o decorator
def admin():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados
    app.run(debug=True)

    