[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/V7V619VJBK)
<p align="right">
<a href="./README.md">English</a> | <a href="./README.pt.md">Portuguese</a>
</p>

#  Ageu Blog Template
This is the template I developed for my personal ["Digital Garden"](https://weeklymusings.net/weekly-musings-092), which I use on my personal [blog](https://ageu.tech/). The idea is for you to be able to use and improve it for your own purposes. I tried to create something clean, simple, and visually pleasing for anyone to use.
Feel free to use it, fork it, and improve it. The code has recently undergone a major security and functionality review, and has been **refactored into a professional modular architecture**.
> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**

##  Overview
The blog offers a clean and responsive layout, optimized for a pleasant reading experience. The structure is designed to be simple to install and maintain, ideal for those looking for a personal and secure writing space. Now with **modular architecture using Flask Blueprints**, making maintenance and scalability easier.
##  Features
- Simple, responsive, and dark-themed design.
- Post editor with [QuillJS](https://quilljs.com/).

- **Enhanced Security:**
-  CSRF protection on all forms.
-  HTML sanitization (XSS) on post content.
-  **Automatic Feed Generation:**
-  Dynamically generated RSS feed (`/feed`).
-  Dynamically generated Sitemap (`/sitemap.xml`) for better SEO.
-  **Modular Architecture:**
-  Clear separation of concerns with Blueprints.
-  Easy maintenance and scalability.
-  Post pagination on homepage and admin panel.
-  Protected admin area with authentication.

  

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
│ ├── __init__.py # Flask factory, initializes blueprints
│ ├── config.py # Application configuration
│ ├── models.py # SQLAlchemy models (User, Post)
│ ├── views.py # Blueprint for public routes
│ ├── admin.py # Blueprint for admin and authentication
│ ├── utils.py # Helper functions (sanitization, auth)
│ │
│ ├── templates/ # Jinja2 templates
│ │ ├── base.html
│ │ ├── index.html
│ │ ├── post.html
│ │ ├── about.html
│ │ ├── login.html
│ │ ├── admin.html
│ │ ├── 404.html
│ │ ├── 500.html
│ │ ├── feed.xml
│ │ └── sitemap.xml
│ │
│ └── static/ # Static files
│ ├── style.css # CSS styles
│ ├── script.js # JavaScript scripts
│ ├── logo.png
│ └── favicon.ico
│
├── run.py # Application entry point
├── requirements.txt # Project dependencies
├── blog.db # SQLite database (generated)
├── README.md # This file
└── README.pt.md # Portuguese version

```  
##  How to Install and Set Up
###  1. Clone the Repository

```bash
git  clone  https://github.com/Ageursilva/ageublog.git
cd  ageublog

```
###  2. Create a Virtual Environment and Install Dependencies
It's crucial to use a virtual environment to isolate project dependencies.
```bash
# Create the environment
python3  -m  venv  venv
# Activate the environment
# On Linux/macOS:
source  venv/bin/activate
# On Windows:
# venv\Scripts\activate
# Install dependencies
pip  install  -r  requirements.txt
```

###  3. Configure the Secret Key

The application needs a `SECRET_KEY` to work. The most secure way is to use environment variables.
**Open the `app/config.py` file** and find the line:
```python
SECRET_KEY  = os.environ.get('SECRET_KEY', 'change-me')
```
To set the environment variable:

**Linux/macOS:**
```bash
export SECRET_KEY=$(python  -c  "import secrets; print(secrets.token_hex(16))")
```
**Windows (PowerShell):**

```powershell
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(16))")
```
Or edit directly in `app/config.py` for local testing.
###  4. Initialize the Database 
With the virtual environment activated, run the following command in your terminal:
```bash
# Creates blog.db file and tables
python  run.py
```
On the first run, Flask will automatically create the database.
###  5. Create an Admin User

Use Python to create your first user.
```bash
python  -c  "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
admin = User(username='your_username')
admin.set_password('your_strong_password')
db.session.add(admin)
db.session.commit()
print('User created successfully!')
"
```

###  6. Run the Application

**Development mode:**
```bash
python run.py
```
**Production mode (with Gunicorn):**
```bash
gunicorn  --workers  4  --bind  0.0.0.0:8000  run:app
```  
Access `http://127.0.0.1:5000` (or `http://127.0.0.1:8000` if using Gunicorn) in your browser.
To access the admin area, go to `/admin/login`.

##  Modular Architecture
The project uses **Flask Blueprints** to organize routes into independent modules:

###  `app/__init__.py` - Factory Pattern

```python
def  create_app():
# Creates and configures the Flask app
# Registers all blueprints
# Initializes extensions (db, csrf)
```
###  `app/models.py` - Data Models

-  `User`: User model with authentication
-  `Post`: Blog post model
- 
###  `app/views.py` - Public Routes

-  `/`: Home with pagination
-  `/post/<id>`: Post page
-  `/about`: About page
-  `/search`: Post search
-  `/feed`: RSS feed
-  `/sitemap.xml`: Sitemap for SEO
- 
###  `app/admin.py` - Admin Routes
-  `/admin/login`: Authentication
-  `/admin/`: Control panel
-  `/admin/create_post`: Create new post
-  `/admin/edit_post/<id>`: Edit post
-  `/admin/delete_post/<id>`: Delete post

###  `app/utils.py` - Helper Functions
-  `login_required()`: Decorator to protect routes
-  `clean_content()`: HTML sanitization
-  `extract_image_and_excerpt()`: Extracts image and excerpt from posts

##  Commenting System
This template has been tested with several commenting solutions. Choose the one that best suits you:
-  **Giscus:** Uses GitHub Discussions. Lightweight, modern, and supports reactions/replies.
-  **Cusdis:** An excellent privacy-focused option that allows anonymous comments.
-  **Utterances:** Uses GitHub Issues. A solid and simple alternative.

To implement, simply replace the comment script at the end of the `templates/post.html` file.
##  Contributions

Contributions are very welcome! Feel free to:
-  Open an issue to report a bug
-  Suggest an improvement
-  Submit a pull request
##  License
This project is licensed under the [Creative Commons BY-NC-SA 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/).
<br>

