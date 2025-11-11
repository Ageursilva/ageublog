import re
import bleach
from bs4 import BeautifulSoup
from functools import wraps
from flask import session, redirect, url_for

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'blockquote', 'pre', 'code', 'ul', 'ol', 'li', 'a', 'img', 'cite']
ALLOWED_ATTRS = {
    'a': ['href', 'rel'],
    'img': ['src', 'alt', 'style', 'width', 'height'],
    '*': ['class'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'data']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def clean_content(content):
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS
    )

def extract_image_and_excerpt(content):
    soup = BeautifulSoup(content, 'html.parser')
    image_tag = soup.find('img')
    image_src = image_tag['src'] if image_tag and image_tag.has_attr('src') else None
    
    if image_tag:
        image_tag.extract()
    
    for p in soup.find_all('p'):
        if any(text in p.get_text() for text in ["Photo by", "Imagem por"]):
            p.extract()
    
    text = soup.get_text()
    excerpt = ' '.join(text.split())[:150]
    
    return image_src, excerpt

def strip_leading_whitespace(html_content):
    if not html_content:
        return ''
    pattern = r'^(\s*(<p[^>]*>(\s|&nbsp;)*</p>|<br\s*/?>)\s*)+'
    return re.sub(pattern, '', html_content.strip(), count=1)
