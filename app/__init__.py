from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    csrf.init_app(app)
    
    # Registrar Blueprints
    from .views import main
    from .admin import admin
    
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    # Template filter
    from .utils import strip_leading_whitespace
    app.template_filter('strip_leading_whitespace')(strip_leading_whitespace)
    
    return app
