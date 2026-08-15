from app.models import Comment


def test_public_pages_render_blog_content(client, seeded_blog):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Primeiro post" in response.data
    assert b"Segundo post" in response.data
    assert b"No Radar" not in response.data


def test_post_page_shows_comments_and_replies(client, seeded_blog):
    response = client.get(f"/post/{seeded_blog['post_id']}")

    assert response.status_code == 200
    assert b"Primeiro post" in response.data
    assert b"Comentario raiz" in response.data
    assert b"Resposta" in response.data
    assert b'<meta name="description" content="Conteudo publico" />' in response.data
    assert b'<link rel="canonical"' in response.data
    assert b'<meta name="twitter:card" content="summary_large_image" />' in response.data


def test_tag_notas_radar_search_feed_and_sitemap(client, seeded_blog):
    checks = [
        f"/tag/{seeded_blog['tag_name']}",
        "/notas",
        f"/notas/{seeded_blog['note_id']}",
        "/radar",
        "/search?query=Primeiro",
        "/feed",
        "/sitemap.xml",
        "/robots.txt",
    ]

    for path in checks:
        response = client.get(path)
        assert response.status_code == 200, path


def test_missing_public_resources_return_404(client):
    for path in ["/post/9999", "/tag/inexistente", "/notas/9999"]:
        assert client.get(path).status_code == 404


def test_create_comment_and_reply(client, app, seeded_blog):
    post_id = seeded_blog["post_id"]

    response = client.post(
        f"/post/{post_id}",
        data={"name": "Maria", "website": "https://example.com", "content": "Gostei"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        comment = Comment.query.filter_by(name="Maria").one()
        assert comment.website == "https://example.com"
        assert comment.parent_id is None

    response = client.post(
        f"/post/{post_id}",
        data={"name": "Joao", "content": "Tambem", "parent_id": seeded_blog["comment_id"]},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        reply = Comment.query.filter_by(name="Joao").one()
        assert reply.parent_id == seeded_blog["comment_id"]


def test_health_reports_ok_with_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["database"] == "ok"


def test_health_returns_503_when_database_is_down(client, monkeypatch):
    """Health check deve falhar (503) quando o banco está fora — e não vazar erro."""

    class BoomSession:
        def execute(self, *a, **k):
            raise Exception("connection refused")

    class BoomDB:
        session = BoomSession()

    monkeypatch.setattr("app.views.db", BoomDB())
    response = client.get("/health")

    assert response.status_code == 503
    body = response.get_json()
    assert body["database"] == "error"
    assert "connection refused" not in response.get_data(as_text=True)


def test_home_has_basic_seo_tags(client, seeded_blog):
    response = client.get("/")

    assert response.status_code == 200
    assert b'<meta name="viewport"' in response.data
    assert b'<link rel="canonical"' in response.data
    assert b'<link rel="alternate" type="application/rss+xml"' in response.data


def test_post_styles_include_quill_rendering_rules(client):
    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert b".post .content .ql-align-center" in response.data
    assert b".post .content .ql-size-huge" in response.data
    assert b".post .content blockquote" in response.data
