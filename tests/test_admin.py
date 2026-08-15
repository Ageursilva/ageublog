from app import db
from app.models import Comment, Note, Post, Tag


def test_admin_requires_login(client):
    response = client.get("/admin/", follow_redirects=False)

    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_login_logout_flow(client, login):
    response = login()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")

    with client.session_transaction() as session:
        assert session["_permanent"] is True
        assert "user_id" in session

    # Logout agora é POST (CSRF-logout)
    response = client.post("/admin/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/login")


def test_create_edit_and_delete_post(client, app, login):
    login()

    response = client.post(
        "/admin/create_post",
        data={"title": "Novo post", "content": "<p>Corpo novo</p>"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        post = Post.query.filter_by(title="Novo post").one()
        post_id = post.id
        assert post.content == "<p>Corpo novo</p>"

    response = client.post(
        f"/admin/edit_post/{post_id}",
        data={"title": "Post editado", "content": "<p>Editado</p>"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Post, post_id).title == "Post editado"

    response = client.post(f"/admin/delete_post/{post_id}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Post, post_id) is None


def test_delete_post_with_comments(client, app, login, seeded_blog):
    """Excluir post com comentários não pode gerar 500 (FK/cascade)."""
    login()
    post_id = seeded_blog["post_id"]

    response = client.post(f"/admin/delete_post/{post_id}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Post, post_id) is None


def test_delete_tag_in_use(client, app, login, seeded_blog):
    """Excluir tag associada a posts não pode gerar 500 (FK/cascade)."""
    login()

    with app.app_context():
        tag = Tag.query.filter_by(name=seeded_blog["tag_name"]).one()
        tag_id = tag.id

    response = client.post(f"/admin/tags/delete/{tag_id}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Tag, tag_id) is None


def test_manage_tags(client, app, login):
    login()

    response = client.post("/admin/tags", data={"name": "dev"}, follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        tag = Tag.query.filter_by(name="dev").one()
        tag_id = tag.id

    response = client.post(f"/admin/tags/delete/{tag_id}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Tag, tag_id) is None


def test_manage_notes(client, app, login):
    login()

    response = client.post("/admin/notas", data={"content": "Nota nova"}, follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        note = Note.query.filter_by(content="Nota nova").one()
        note_id = note.id

    response = client.post(
        f"/admin/notas/edit/{note_id}",
        data={"content": "Nota editada"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Note, note_id).content == "Nota editada"

    response = client.post(f"/admin/notas/delete/{note_id}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Note, note_id) is None


def test_manage_comments(client, app, login, seeded_blog):
    login()

    response = client.get("/admin/comments")
    assert response.status_code == 200
    assert b"Comentario raiz" in response.data

    response = client.post(f"/admin/comments/seen/{seeded_blog['post_id']}", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Comment, seeded_blog["comment_id"]).seen is True

    response = client.post(
        f"/admin/comments/delete/{seeded_blog['reply_id']}",
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Comment, seeded_blog["reply_id"]) is None
