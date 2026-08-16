from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError
from .models import User, Post, Tag, Note, Comment
from . import db, limiter
from .utils import login_required, clean_content, replace_inline_images_with_supabase, log_upload_exception
import bleach

admin = Blueprint('admin', __name__)


@admin.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute; 100 per hour", methods=["POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user is None:
            # Equaliza o tempo de resposta (evita enumeração de usuário por timing).
            dummy = User(username=username)
            dummy.set_password('dummy-password-for-timing')
            user = dummy

        if user.check_password(password):
            session.clear()
            session.permanent = True
            session['user_id'] = user.id
            return redirect(url_for('admin.admin_panel'))
        else:
            flash('Nome de usuário ou senha incorretos', 'error')

    return render_template('login.html', csrf_token_value=generate_csrf())


@admin.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin.route('/', methods=['GET'])
@login_required
def admin_panel():
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Post.query.order_by(Post.created_at.desc())
    if search:
        query = query.filter(Post.title.ilike(f'%{search}%'))

    posts = query.paginate(
        page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 6), error_out=False
    )

    prev_url = url_for('admin.admin_panel', page=posts.prev_num, q=search) if posts.has_prev else None
    next_url = url_for('admin.admin_panel', page=posts.next_num, q=search) if posts.has_next else None

    return render_template(
        'admin.html',
        posts=posts.items,
        pagination=posts,
        prev_url=prev_url,
        next_url=next_url,
        search=search,
        csrf_token_value=generate_csrf()
    )


@admin.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = bleach.clean(request.form.get('title', '').strip())
        content = clean_content(request.form.get('content', ''))
        tag_ids = request.form.getlist('tags')

        if not title or not content:
            flash('Título e conteúdo são obrigatórios', 'error')
            return redirect(url_for('admin.create_post'))

        if len(title) > 255:
            # A coluna é varchar(255) — no Postgres um título maior levanta
            # DataError e derruba a requisição com 500.
            flash('Título muito longo (máximo 255 caracteres)', 'error')
            return redirect(url_for('admin.create_post'))

        new_post = Post(title=title, content=content)

        if tag_ids:
            new_post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

        db.session.add(new_post)
        db.session.flush()

        try:
            updated_content, _ = replace_inline_images_with_supabase(
                new_post.content, new_post.id
            )
            new_post.content = updated_content
        except Exception as exc:
            log_upload_exception(exc, new_post.id)
            db.session.rollback()
            flash(f'Falha ao enviar imagens: {exc}', 'error')
            return redirect(url_for('admin.create_post'))
        db.session.commit()

        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('admin.admin_panel'))

    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin.html', creating_new_post=True, all_tags=all_tags, csrf_token_value=generate_csrf())


@admin.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)

    if request.method == 'POST':
        post.title = bleach.clean(request.form.get('title', '').strip())
        post.content = clean_content(request.form.get('content', ''))
        tag_ids = request.form.getlist('tags')

        if not post.title or not post.content:
            flash('Título e conteúdo são obrigatórios', 'error')
            return redirect(url_for('admin.edit_post', post_id=post_id))

        if len(post.title) > 255:
            flash('Título muito longo (máximo 255 caracteres)', 'error')
            return redirect(url_for('admin.edit_post', post_id=post_id))

        post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all() if tag_ids else []

        try:
            updated_content, _ = replace_inline_images_with_supabase(
                post.content, post.id
            )
            post.content = updated_content
        except Exception as exc:
            log_upload_exception(exc, post.id)
            db.session.rollback()
            flash(f'Falha ao enviar imagens: {exc}', 'error')
            return redirect(url_for('admin.edit_post', post_id=post_id))

        db.session.commit()
        flash('Post atualizado com sucesso!', 'success')
        return redirect(url_for('admin.admin_panel'))

    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin.html', post_to_edit=post, all_tags=all_tags, csrf_token_value=generate_csrf())


@admin.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    if request.method == 'POST':
        name = bleach.clean(request.form.get('name', '').strip())
        if len(name) > 100:
            # A coluna é varchar(100) — no Postgres um nome maior dá 500.
            flash('Nome de tag muito longo (máximo 100 caracteres)', 'error')
        elif name:
            existing = Tag.query.filter_by(name=name).first()
            if not existing:
                db.session.add(Tag(name=name))
                db.session.commit()
                flash('Tag criada!', 'success')
            else:
                flash('Tag já existe', 'error')
        return redirect(url_for('admin.manage_tags'))

    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin_tags.html', tags=all_tags, csrf_token_value=generate_csrf())


@admin.route('/tags/delete/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = db.get_or_404(Tag, tag_id)
    try:
        db.session.delete(tag)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir: a tag está em uso por posts.', 'error')
    else:
        flash('Tag excluída!', 'success')
    return redirect(url_for('admin.manage_tags'))


@admin.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    try:
        db.session.delete(post)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir: o post possui comentários associados.', 'error')
    else:
        flash('Post excluído com sucesso!', 'success')
    return redirect(url_for('admin.admin_panel'))


@admin.route('/comments')
@login_required
def comments():
    posts_with_comments = db.session.query(Post).join(
        Comment, Comment.post_id == Post.id
    ).distinct().order_by(Post.id.desc()).all()

    posts_data = []
    for post in posts_with_comments:
        post_comments = Comment.query.filter_by(
            post_id=post.id,
            parent_id=None
        ).order_by(Comment.created_at.asc()).all()

        has_unseen = any(not c.seen for c in post_comments)
        posts_data.append({
            'post': post,
            'comments': post_comments,
            'has_unseen': has_unseen
        })

    return render_template('admin_comments.html',
                           posts_data=posts_data,
                           csrf_token_value=generate_csrf())


@admin.route('/comments/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    try:
        db.session.delete(comment)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir: o comentário possui respostas.', 'error')
    return redirect(url_for('admin.comments'))


@admin.route('/comments/seen/<int:post_id>', methods=['POST'])
@login_required
def mark_seen(post_id):
    Comment.query.filter_by(post_id=post_id, seen=False).update({'seen': True})
    db.session.commit()
    return redirect(url_for('admin.comments'))


@admin.route('/notas', methods=['GET', 'POST'])
@login_required
def admin_notas():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            note = Note(content=content)
            db.session.add(note)
            db.session.commit()
            flash('Nota criada!', 'success')
        return redirect(url_for('admin.admin_notas'))

    page = request.args.get('page', 1, type=int)
    notes = Note.query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('admin_notas.html', notes=notes.items,
                           pagination=notes, csrf_token_value=generate_csrf())


@admin.route('/notas/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_nota(note_id):
    note = db.get_or_404(Note, note_id)
    db.session.delete(note)
    db.session.commit()
    flash('Nota excluída!', 'success')
    return redirect(url_for('admin.admin_notas'))


@admin.route('/notas/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_nota(note_id):
    note = db.get_or_404(Note, note_id)
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            note.content = content
            note.updated_at = db.func.now()
            db.session.commit()
            flash('Nota atualizada!', 'success')
            return redirect(url_for('admin.admin_notas'))
    return render_template('admin_notas.html', notes=[], pagination=None,
                           edit_note=note, csrf_token_value=generate_csrf())