[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/V7V619VJBK)
<p align="right">
<a href="./README.md">English</a> | <a href="./README.pt.md">Portuguese</a>
</p>

#  Ageu Blog Template
This is the template I developed for my personal ["Digital Garden"](https://weeklymusings.net/weekly-musings-092), which I use on my personal [blog](https://ageu.blog/). The idea is for you to be able to use and improve it for your own purposes. I tried to create something clean, simple, and visually pleasing for anyone to use.
Feel free to use it, fork it, and improve it. The code is built with security and performance in mind and follows a **professional modular architecture**.
> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**

##  Overview
The blog offers a clean and responsive layout, optimized for a pleasant reading experience. The structure is designed to be simple to install and maintain, ideal for those looking for a personal and secure writing space. Now with **modular architecture using Flask Blueprints**, making maintenance and scalability easier.
##  Features

**Content**
- Posts with a rich text editor ([QuillJS](https://quilljs.com/)).
- Tags to organize posts (`/tag/<name>`).
- Notes — short Markdown posts (`/notas`).
- Radar Cultural — a pinned post for cultural recommendations.
- Full-text search (`/search?query=...`).
- Pagination on the homepage, tags and admin panel.

**Comments**
- Native comment system (no third-party service): replies, author badge,
  and a moderation queue in the admin panel.

**Security**
- CSRF protection on all forms (Flask-WTF).
- HTML sanitization (Bleach) on post content and comment fields.
- Server-side validation of the comment `website` field (blocks `javascript:`/`data:`).
- Rate limiting on login and comments (per real IP, behind proxies).
- Secure sessions (HttpOnly, SameSite, Secure in production) and POST-only logout.
- Runs as a non-root service in production.

**Performance & SEO**
- Dynamically generated RSS feed (`/feed`).
- Dynamically generated sitemap (`/sitemap.xml`).
- JSON-LD structured data (`BlogPosting`) on posts.
- Inline SVG icons — no icon CDN.
- Static files served directly by Nginx with cache (production).

**Architecture**
- Modular Flask app with the application factory pattern and Blueprints.
- SQLite by default; PostgreSQL/Supabase optional.
- Minimal, clean, dark-themed design — no heavy CSS frameworks.

##  Technologies Used
-  **Backend**: Python, Flask, Jinja2
-  **Database**: SQLAlchemy, SQLite
-  **Frontend**: HTML5, CSS3, JavaScript
-  **Security**: Flask-WTF (CSRF), Bleach (XSS)
-  **Editor**: QuillJS

##  Project Structure

```
ageublog/
│
├── app/
│   ├── __init__.py      # Flask factory, blueprints, security config
│   ├── config.py        # Configuration (env-based)
│   ├── models.py        # SQLAlchemy models (User, Post, Comment, Tag, Note)
│   ├── views.py         # Public routes (Blueprint)
│   ├── admin.py         # Admin routes + authentication
│   ├── utils.py         # Helpers (sanitization, auth, image upload)
│   │
│   ├── templates/       # Jinja2 templates (posts, admin, feed, sitemap...)
│   └── static/          # style.css, script.js, favicon.ico
│
├── run.py               # Application entry point
├── requirements.txt     # Dependencies
├── requirements-dev.txt # Dev/test dependencies (pytest)
├── .env.example         # Environment variables template
├── LICENSE
└── README.md / README.pt.md
```
##  How to Install and Set Up

###  1. Clone the Repository

```bash
git clone https://github.com/Ageursilva/ageublog.git
cd ageublog
```

###  2. Create a Virtual Environment and Install Dependencies

```bash
python3 -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

pip install -r requirements.txt
# Optional, to run the test suite:
pip install -r requirements-dev.txt
```

###  3. Configure the Environment (`.env`)

The application needs a `SECRET_KEY` and **refuses to start without one**.
Copy the example file and set your values:

```bash
cp .env.example .env
```

Then edit `.env` and set `SECRET_KEY` to a strong random value
(e.g. `python -c 'import secrets; print(secrets.token_hex(32))'`).

By default the app uses **SQLite** (`sqlite:///app/blog.db`) — no external
database is needed to get started. To use PostgreSQL/Supabase, set
`DATABASE_URL` in `.env` (see `.env.example` for all options).

###  4. Create the Database and the Admin User

Run once to create the tables and your admin account:

```bash
python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('your_strong_password')
        db.session.add(admin)
        db.session.commit()
        print('Admin created: admin')
    else:
        print('Admin already exists')
"
```

###  5. Run the Application

**Development:**
```bash
python run.py
```
**Production (Gunicorn):**
```bash
gunicorn --workers 2 --bind 0.0.0.0:8000 run:app
```
Access `http://127.0.0.1:5000` (or `http://127.0.0.1:8000` with Gunicorn).
Admin area: `/admin/login`.

##  Running the Tests

The project includes an automated test suite (pytest):

```bash
pip install -r requirements-dev.txt
pytest
```

It covers security (XSS sanitization, CSRF, rate limits), public routes,
and the admin CRUD flows.

##  Modular Architecture

The project uses **Flask Blueprints** to organize routes into independent modules:

###  `app/__init__.py` - Factory Pattern

```python
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix="/admin")
    return app
```

###  `app/models.py` - Data Models

- `User`: Admin user with password authentication.
- `Post`: Blog post (title, content, tags).
- `Comment`: Post comments (with replies and author badge).
- `Tag`: Post tags.
- `Note`: Short Markdown posts.

###  `app/views.py` - Public Routes

- `/`: Home with pagination.
- `/post/<id>`: Post page with comments.
- `/tag/<name>`: Posts by tag.
- `/notas` / `/notas/<id>`: Notes.
- `/radar`: Radar Cultural.
- `/search`: Post search.
- `/feed`: RSS feed.
- `/sitemap.xml`: Sitemap for SEO.
- `/about`, `/privacidade`: Static pages.

###  `app/admin.py` - Admin Routes

- `/admin/login`: Authentication (rate limited).
- `/admin/`: Control panel.
- `/admin/create_post` / `/admin/edit_post/<id>` / `/admin/delete_post/<id>`: Post management.
- `/admin/tags`: Tag management.
- `/admin/comments`: Comment moderation.
- `/admin/notas`: Notes management.

###  `app/utils.py` - Helper Functions

- `login_required()`: Decorator to protect routes.
- `clean_content()`: HTML sanitization (Bleach).
- `extract_image_and_excerpt()`: Extracts image and excerpt from posts.
- `sanitize_website()`: Validates comment website URLs.

##  Commenting System

Native comment system (no third-party service):

- Visitors can comment on posts, with optional name and website.
- Replies to comments (one level).
- Comments from the admin are marked with an author badge.
- Moderation queue in the admin panel (`/admin/comments`): mark as seen or delete.
- Server-side validation: the `website` field only accepts `http`/`https`
  (blocks `javascript:`/`data:`), and content length is limited.

##  Contributions

Contributions are very welcome! Feel free to:
-  Open an issue to report a bug
-  Suggest an improvement
-  Submit a pull request
##  License
This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html). See the `LICENSE` file for details.
<br>

