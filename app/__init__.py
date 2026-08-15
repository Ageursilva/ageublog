import os
from flask import Flask, abort, request
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import markdown as md
from .utils import clean_content, validate_supabase_env, strip_leading_whitespace


db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

def create_app(test_config=None):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(base_dir, "..", ".env"))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )
    # Atrás do Nginx (única entrada), o X-Forwarded-For é confiável —
    # necessário para o rate limit enxergar o IP real do cliente.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    app.config.from_object('app.config.Config')
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY ausente — defina no ambiente/.env. "
            "Sem ela as sessões podem ser forjadas."
        )

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from .views import main
    from .admin import admin

    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')

    app.template_filter('strip_leading_whitespace')(strip_leading_whitespace)

    @app.template_filter('markdown')
    def markdown_filter(text):
        # Sanitiza também o HTML cru embutido no Markdown (defesa em profundidade).
        return clean_content(md.markdown(text, extensions=['nl2br', 'fenced_code']))

    @app.before_request
    def validate_host():
        host = request.host.split(":")[0]
        if host not in app.config.get("TRUSTED_HOSTS", []):
            abort(400)

    validate_supabase_env(app)
    return app