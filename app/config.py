import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'coloque_sua_chave_aqui')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    POSTS_PER_PAGE = 6
    
