import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    csrf.init_app(app)
    
    from .views import main
    from .admin import admin

    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    from .utils import strip_leading_whitespace
    app.template_filter('strip_leading_whitespace')(strip_leading_whitespace)
    
    return app
