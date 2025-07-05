# Ageu Blog Template
This is the template I developed for my personal ["Digital Garden"](https://weeklymusings.net/weekly-musings-092), which I use on my personal [blog](https://ageu.tech/). The idea is for you to be able to use and improve it for your own purposes. I tried to create something clean, simple, and visually pleasing for anyone to use.

Feel free to use it, fork it, and improve it. The code has recently undergone a major security and functionality review, so I'd call this a V2(?).

> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**

## Overview
The blog offers a clean and responsive layout, optimized for a pleasant reading experience. The structure is designed to be simple to install and maintain, ideal for those looking for a personal and secure writing space.

## Features
- ✅ Simple, responsive, and dark-themed design.
- ✍️ Post editor with [QuillJS](https://quilljs.com/).
- 🔒 **Enhanced Security:**
    - CSRF protection on all forms.
    - HTML sanitization (XSS) on post content.
- ⚙️ **Automatic Feed Generation:**
    - Dynamically generated RSS feed (`/feed`).
    - Dynamically generated Sitemap (`/sitemap.xml`) for better SEO.
	- Post pagination on the homepage and admin panel.
	- Protected admin area with authentication.
## Technologies Used
- **Backend**: Python, Flask, Jinja2
- **Database**: SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Flask-WTF (CSRF), Bleach (XSS)
- **Editor**: QuillJS

## How to Install and Set Up

### 1. Clone the Repository
```
git clone https://github.com/Ageursilva/ageublog.git
cd ageublog
```
### 2. Create a Virtual Environment and Install Dependencies
It's crucial to use a virtual environment to isolate project dependencies.
```bash
# Create the environment
python3 -m venv venv
# Activate the environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 3. Configure the Secret Key
The application needs a `SECRET_KEY` to work. The most secure way is to use environment variables, but for a quick start, you can edit it directly.

**Open the `app.py` file** and find the line:
`app.config['SECRET_KEY'] = 'your_key_here'`

Replace `'your_key_here'` with a strong key. To generate one, use the Python terminal:
```python
import secrets; print(secrets.token_hex(16))
```

### 4. Initialize the Database
With the virtual environment activated, run the following command in your terminal:
```bash
# This command uses the application context to create the .db file and tables.
python -c "from app import db; from app.models import User, Post; db.create_all()"
```
*Note: If you have already modularized the project, adjust the import paths as needed.*

### 5. Create an Admin User
Use the Flask shell to create your first user.
```bash
flask shell
```
Inside the shell, execute the following code:
```python
# Import the necessary tools
from app import db
from app.models import User # Or import from app if not modularized

# Create the user
admin = User(username='your_username')
admin.set_password('your_strong_password')

# Save to the database
db.session.add(admin)
db.session.commit()

# Exit the shell with exit()
exit()
```

### 6. Run the Application
```bash
flask run
```
Access `http://127.0.0.1:5000` in your browser. To access the admin area, go to `/login`.

## Commenting System
This template has been tested with several commenting solutions. Choose the one that best suits you:

- **Giscus:** Uses GitHub Discussions. Lightweight, modern, and supports reactions/replies.
- **Cusdis:** An excellent privacy-focused option that allows anonymous comments.
- **Utterances:** Uses GitHub Issues. A solid and simple alternative.

To implement, simply replace the comment script at the end of the `templates/post.html` file.

## Contributions
Contributions are very welcome! Feel free to open an issue to report a bug or suggest an improvement, or submit a pull request.

## License
This project is licensed under the [Creative Commons BY-NC-SA 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/).
<br>
## Contributors
<table align="center">
  <tr>
    <td align="center">
      <a href="https://www.linkedin.com/in/ageursilva/">
        <img src="https://github.com/Ageursilva.png" width="100px;" alt="Ageu Silva"/><br />
        <sub><b>Ageu Silva</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://www.linkedin.com/in/vitor-alvim-604080319">
        <img src="https://media.licdn.com/dms/image/v2/D4D03AQF0SMMjk3UIeA/profile-displayphoto-shrink_800_800/B4DZY7t8YkG4Ac-/0/1744758622504?e=1756944000&v=beta&t=yYcfOzQWCWoHKBYZH9Qe6BBIQiToa_Y_ljLEHIPdnbc" width="100px;" alt="Vitor Alvim"/><br />
        <sub><b>Vitor Alvim</b></sub>
      </a>
    </td>
  </tr>
</table>

<p align="center">
<a href="https://github.com/Ageursilva/ageublog">
<img src="https://img.shields.io/github/forks/Ageursilva/ageublog?style=social&label=Fork" alt="Forks">
</a>
<a href="https://github.com/Ageursilva/ageublog">
<img src="https://img.shields.io/github/stars/Ageursilva/ageublog?style=social&label=Star" alt="Stars">
</a>
<img src="https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg" alt="License: CC BY-NC-SA 4.0">
<img src="https://img.shields.io/badge/Status-In_Development-yellow.svg" alt="Status: In Development">
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
<img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
</p>
