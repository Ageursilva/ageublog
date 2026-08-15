from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'), passive_deletes=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id', ondelete='CASCADE'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_author = db.Column(db.Boolean, default=False)
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    # lazy='selectin' evita N+1 ao listar respostas de cada comentário.
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side='Comment.id'), lazy='selectin', order_by='Comment.created_at')
    
class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())