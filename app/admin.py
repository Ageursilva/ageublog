from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import generate_csrf
from .models import User, Post
from . import db
from .utils import login_required, clean_content
import bleach

admin = Blueprint('admin', __name__)

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('admin.admin_panel'))
        else:
            flash('Nome de usuário ou senha incorretos', 'error')
    
    return render_template('login.html', csrf_token_value=generate_csrf())

@admin.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('admin.login'))

@admin.route('/', methods=['GET'])
@login_required
def admin_panel():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    return render_template(
        'admin.html',
        posts=posts.items,
        pagination=posts,
        csrf_token_value=generate_csrf()
    )

@admin.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = bleach.clean(request.form.get('title', '').strip())
        content = clean_content(request.form.get('content', ''))
        
        if not title or not content:
            flash('Título e conteúdo são obrigatórios', 'error')
            return redirect(url_for('admin.create_post'))
        
        new_post = Post(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        
        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('admin.admin_panel'))
    
    return render_template('admin.html', creating_new_post=True, csrf_token_value=generate_csrf())

@admin.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = bleach.clean(request.form.get('title', '').strip())
        post.content = clean_content(request.form.get('content', ''))
        
        if not post.title or not post.content:
            flash('Título e conteúdo são obrigatórios', 'error')
            return redirect(url_for('admin.edit_post', post_id=post_id))
        
        db.session.commit()
        flash('Post atualizado com sucesso!', 'success')
        return redirect(url_for('admin.admin_panel'))
    
    return render_template('admin.html', post_to_edit=post, csrf_token_value=generate_csrf())

@admin.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post excluído com sucesso!', 'success')
    return redirect(url_for('admin.admin_panel'))
