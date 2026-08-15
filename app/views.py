from bs4 import BeautifulSoup
from flask import (
    Blueprint, render_template, request, make_response, send_from_directory,
    redirect, url_for, session, jsonify, flash, current_app,
)
from . import db, limiter
from .models import Post, Comment, Tag, Note
from .utils import extract_image_and_excerpt, sanitize_website


main = Blueprint('main', __name__)


def _posts_with_data(posts):
    """Monta a lista de posts com imagem/excerpt sem reparsear o HTML."""
    result = []
    for post in posts:
        image_url, excerpt = extract_image_and_excerpt(post.content)
        result.append({'post': post, 'image_url': image_url, 'excerpt': excerpt})
    return result


@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter(Post.title != "No Radar").order_by(
        Post.id.desc()
    ).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    posts_with_data = _posts_with_data(pagination.items)
    return render_template('index.html', posts=posts_with_data, pagination=pagination)


@main.route('/tag/<string:tag_name>')
def tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = tag.posts.filter(Post.title != "No Radar").order_by(
        Post.id.desc()
    ).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    posts_with_data = _posts_with_data(pagination.items)
    return render_template('tag.html', tag=tag, posts=posts_with_data, pagination=pagination)


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def post(post_id):
    post = db.get_or_404(Post, post_id)
    image_url, excerpt = extract_image_and_excerpt(post.content)
    is_logged = 'user_id' in session

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        website = sanitize_website(request.form.get('website', ''))
        content = request.form.get('content', '').strip()
        parent_id = request.form.get('parent_id', type=int)

        errors = []
        if not name:
            errors.append('Informe seu nome.')
        elif len(name) > 100:
            errors.append('Nome muito longo (máximo 100 caracteres).')
        if not content:
            errors.append('Escreva um comentário.')
        elif len(content) > 1000:
            errors.append('Comentário muito longo (máximo 1000 caracteres).')
        if parent_id:
            parent = db.session.get(Comment, parent_id)
            if not parent or parent.post_id != post_id or parent.parent_id is not None:
                errors.append('Resposta inválida.')
                parent_id = None

        if errors:
            flash(' '.join(errors), 'error')
            return redirect(url_for('main.post', post_id=post_id))

        comment = Comment(
            post_id=post_id,
            parent_id=parent_id or None,
            name=name,
            website=website,
            content=content,
            is_author=is_logged
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('main.post', post_id=post_id))

    comments = Comment.query.filter_by(
        post_id=post_id,
        parent_id=None
    ).order_by(Comment.created_at.asc()).all()

    return render_template('post.html', post=post, image_url=image_url,
                           excerpt=excerpt, comments=comments, is_logged=is_logged)


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()

    if not query:
        return render_template('search_results.html', query=query, results=[])

    results = Post.query.filter(
        (Post.title.ilike(f'%{query}%')) | (Post.content.ilike(f'%{query}%'))
    ).all()

    return render_template('search_results.html', query=query, results=results)


@main.route('/radar')
def radar():
    radar_post = Post.query.filter_by(title="No Radar").first()
    if not radar_post:
        return render_template('radar_placeholder.html'), 404
    return render_template('radar.html', post=radar_post)


@main.route('/robots.txt')
def serve_robots():
    return send_from_directory(current_app.static_folder, 'robots.txt')


@main.route('/sitemap.xml')
def sitemap():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    tags = Tag.query.order_by(Tag.name).all()
    template = render_template('sitemap.xml', posts=posts, tags=tags)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response


@main.route('/feed')
def feed():
    posts = Post.query.filter(Post.title != "No Radar").order_by(Post.created_at.desc()).all()
    posts_data = []

    for post in posts:
        soup = BeautifulSoup(post.content, 'html.parser')

        for p in soup.find_all('p'):
            if any(text in p.get_text() for text in ["Photo by", "Imagem por"]):
                p.extract()

        first_img = soup.find('img')
        image_url = first_img['src'] if first_img and first_img.get('src') else None

        posts_data.append({
            'post': post,
            # Fecha a sequência ]]> dentro do CDATA do feed para não quebrar o XML.
            'description': str(soup).replace(']]>', ']]]]><![CDATA[>'),
            'image_url': image_url,
        })

    template = render_template('feed.xml', posts=posts, posts_data=posts_data)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response


@main.route('/health')
def health():
    db_status = 'ok'
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_status = 'error'

    response = jsonify({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'database': db_status,
        'version': '1.0'
    })
    if db_status != 'ok':
        response.status_code = 503
    return response


@main.route('/notas')
def notas():
    page = request.args.get('page', 1, type=int)
    pagination = Note.query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('notas.html', notes=pagination.items, pagination=pagination)


@main.route('/notas/<int:note_id>')
def nota(note_id):
    note = db.get_or_404(Note, note_id)
    return render_template('nota.html', note=note)


@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


@main.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')