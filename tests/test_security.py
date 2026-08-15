from app import db
from app.models import Comment, Post, User


def test_login_rejects_invalid_password(client, seeded_blog):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Nome de usu" in response.data


def test_admin_session_expires_after_two_hours(app):
    assert app.permanent_session_lifetime.total_seconds() == 2 * 60 * 60


def test_admin_post_requires_csrf_when_enabled(app, client, seeded_blog):
    app.config["WTF_CSRF_ENABLED"] = True

    with client.session_transaction() as session:
        session["user_id"] = seeded_blog["user_id"]

    response = client.post(
        "/admin/create_post",
        data={"title": "Sem CSRF", "content": "<p>x</p>"},
        follow_redirects=False,
    )

    assert response.status_code == 400


def test_public_comment_requires_csrf_when_enabled(app, client, seeded_blog):
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "Sem csrf", "content": "bloqueado"},
        follow_redirects=False,
    )

    assert response.status_code == 400


def test_admin_session_login_marks_author_comments(client, app, login, seeded_blog):
    login()

    response = client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "Ageu", "content": "Resposta do autor"},
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        admin_user = db.session.execute(
            db.select(User).filter_by(username="admin")
        ).scalar_one()
        assert admin_user.username == "admin"
        assert Comment.query.filter_by(name="Ageu").one().is_author is True


def test_comment_website_is_sanitized(client, app, seeded_blog):
    """Campo website não pode carregar javascript:/data: (stored XSS)."""
    response = client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "Atacante", "website": "javascript:alert(1)", "content": "oi"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        assert Comment.query.filter_by(name="Atacante").one().website is None

    # URL sem esquema é normalizada para https
    client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "Maria", "website": "example.com", "content": "oi2"},
        follow_redirects=False,
    )
    with app.app_context():
        assert Comment.query.filter_by(name="Maria").one().website == "https://example.com"


def test_comment_length_and_parent_validation(client, app, seeded_blog):
    # conteúdo acima de 1000 caracteres é rejeitado
    response = client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "Spam", "content": "x" * 1001},
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        assert Comment.query.filter_by(name="Spam").first() is None

    # resposta para comentário de outro post é rejeitada
    with app.app_context():
        other_post = Post(title="Outro post", content="<p>outro</p>")
        db.session.add(other_post)
        db.session.commit()
        other_comment = Comment(
            post_id=other_post.id, name="Outro", content="comentario"
        )
        db.session.add(other_comment)
        db.session.commit()
        other_comment_id = other_comment.id

    client.post(
        f"/post/{seeded_blog['post_id']}",
        data={"name": "X", "content": "oi", "parent_id": str(other_comment_id)},
        follow_redirects=False,
    )
    with app.app_context():
        assert Comment.query.filter_by(name="X").first() is None


def test_bleach_strips_scripts_and_event_handlers(client, app, login):
    """Conteúdo de post é sanitizado no servidor (XSS via Quill/admin)."""
    login()
    response = client.post(
        "/admin/create_post",
        data={
            "title": "XSS test",
            "content": (
                '<p>ok</p><script>alert(1)</script>'
                '<img src="x" onerror="alert(2)">'
                '<a href="javascript:alert(3)">link</a>'
                '<a href="data:text/html,<script>alert(4)</script>">data</a>'
            ),
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        post = Post.query.filter_by(title="XSS test").one()
        assert "<script" not in post.content
        assert "onerror" not in post.content
        assert "javascript:" not in post.content
        assert 'href="data:' not in post.content
        assert "<p>ok</p>" in post.content
