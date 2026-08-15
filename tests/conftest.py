import pytest

from app import create_app, db
from app.models import Comment, Note, Post, Tag, User


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.admin.replace_inline_images_with_supabase",
        lambda content, post_id: (content, 0),
    )

    flask_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
            "SECRET_KEY": "test-secret",
            "POSTS_PER_PAGE": 2,
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_blog(app):
    with app.app_context():
        user = User(username="admin")
        user.set_password("correct-password")

        python = Tag(name="python")
        flask = Tag(name="flask")
        first = Post(title="Primeiro post", content="<p>Conteudo publico</p>")
        second = Post(title="Segundo post", content="<p>Outro texto</p>")
        radar = Post(title="No Radar", content="<p>Filme bom</p>")
        note = Note(content="Uma nota curta")

        first.tags.append(python)
        second.tags.append(flask)

        db.session.add_all([user, python, flask, first, second, radar, note])
        db.session.flush()

        comment = Comment(post_id=first.id, name="Leitor", content="Comentario raiz")
        db.session.add(comment)
        db.session.flush()
        reply = Comment(
            post_id=first.id,
            parent_id=comment.id,
            name="Autor",
            content="Resposta",
            is_author=True,
        )
        db.session.add(reply)
        db.session.commit()

        return {
            "user_id": user.id,
            "post_id": first.id,
            "second_post_id": second.id,
            "radar_id": radar.id,
            "tag_name": python.name,
            "note_id": note.id,
            "comment_id": comment.id,
            "reply_id": reply.id,
        }


@pytest.fixture
def login(client, seeded_blog):
    def _login():
        return client.post(
            "/admin/login",
            data={"username": "admin", "password": "correct-password"},
            follow_redirects=False,
        )

    return _login
