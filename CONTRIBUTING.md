# Contributing

Thank you for your interest in contributing to this project! This guide will
help you set up the development environment and ensure your contributions
match the project's standards.

## Requirements

- Python 3.8+
- Flask
- SQLite (default, for development) or PostgreSQL/Supabase
- Other dependencies listed in `requirements.txt`

## Environment Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Ageursilva/ageublog.git
    cd ageublog
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate   # Linux/macOS
    venv\Scripts\activate      # Windows
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt   # for the test suite
    ```

4. **Configure the environment**:
   Copy `.env.example` to `.env` and set at least `SECRET_KEY` (the app
   refuses to start without it):
    ```bash
    cp .env.example .env
    ```

5. **Create the database and the admin user** (first time only):
    ```bash
    python -c "
    from app import create_app, db
    from app.models import User
    app = create_app()
    with app.app_context():
        db.create_all()
        admin = User(username='admin')
        admin.set_password('your_strong_password')
        db.session.add(admin)
        db.session.commit()
        print('Admin created: admin')
    "
    ```

6. **Run the application**:
    ```bash
    python run.py
    ```
    The project will be available at `http://localhost:5000`.

## Project Structure

- `app/`: Flask application package (factory, models, views, admin, utils).
- `app/templates/`: Jinja2 templates.
- `app/static/`: Static files (CSS, JS, icons).
- `run.py`: Application entry point.
- `tests/`: Automated tests (pytest).
- `requirements.txt` / `requirements-dev.txt`: Dependencies.

## Running the Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Contributing Code

1. **Fork the repository** and create a new branch:
    ```bash
    git checkout -b your-feature-branch
    ```

2. **Write clean, documented code**:
   - Follow PEP 8 for Python.
   - Comment code sections that may not be clear to other developers.
   - Keep the project's HTML/CSS formatting style for consistency.

3. **Add tests** (when applicable):
   - Write unit tests for new features or bug fixes.
   - Make sure all tests pass before submitting.

4. **Update the documentation**:
   - If your change adds or modifies a feature, update the relevant docs.

5. **Commit and push**:
    ```bash
    git commit -m "Clear commit description"
    git push origin your-feature-branch
    ```

6. **Open a Pull Request**:
   - Explain what was added or changed and why.
   - Wait for feedback and adjust if needed.

## Commit Conventions

- `feat`: New feature.
- `fix`: Bug fix.
- `docs`: Documentation changes.
- `style`: Formatting changes (spaces, semicolons, etc).
- `refactor`: Code refactoring without behavior change.
- `test`: Adding or modifying tests.

Example:
```bash
git commit -m "feat: add notes feature to the admin panel"
```