from flask import Blueprint, render_template, request, make_response, send_from_directory
from .models import Post
from .utils import extract_image_and_excerpt
from bs4 import BeautifulSoup
from flask import current_app

main = Blueprint('main', __name__)

@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter(Post.title != "No Radar").order_by(
        Post.id.desc()
    ).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    posts_with_data = [
        {
            'post': post,
            'image_url': extract_image_and_excerpt(post.content)[0],
            'excerpt': extract_image_and_excerpt(post.content)[1]
        }
        for post in pagination.items
    ]
    
    return render_template('index.html', posts=posts_with_data, pagination=pagination)

@main.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

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
    template = render_template('sitemap.xml', posts=posts)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

@main.route('/feed')
def feed():
    posts = Post.query.filter(Post.title != "No Radar").order_by(Post.created_at.desc()).all()
    posts_data = []
    
    for post in posts:
        soup = BeautifulSoup(post.content, 'html.parser')
        
        for img_tag in soup.find_all('img'):
            img_tag.decompose()
        
        for p in soup.find_all('p'):
            if any(text in p.get_text() for text in ["Photo by", "Imagem por"]):
                p.extract()
        
        posts_data.append({
            'post': post,
            'description': str(soup),
        })
    
    template = render_template('feed.xml', posts=posts, posts_data=posts_data)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500
