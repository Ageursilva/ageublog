import os
import re
import time
import base64
import tempfile
from functools import wraps
from urllib.parse import urlsplit

import bleach
import requests
from bleach.css_sanitizer import CSSSanitizer
from bs4 import BeautifulSoup
from flask import session, redirect, url_for
from flask import current_app

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'blockquote', 'pre', 'code', 'ul', 'ol', 'li', 'a', 'img', 'cite']
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'data']
ALLOWED_CSS_PROPERTIES = [
    "width",
    "height",
    "max-width",
    "max-height",
    "display",
    "margin",
]
CSS_SANITIZER = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)


def _allowed_attrs(tag, name, value):
    """Filtro de atributos do bleach: mantém apenas o essencial e impede
    hrefs com esquema perigoso (ex.: data:) em links, mesmo com 'data'
    liberado globalmente para imagens base64."""
    if name == "class":
        return value
    if tag == "a":
        if name == "href":
            scheme = urlsplit(value).scheme.lower()
            return value if scheme in ("", "http", "https", "mailto") else None
        if name == "rel":
            return value
        return None
    if tag == "img" and name in ("src", "alt", "style", "width", "height"):
        return value
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def clean_content(content):
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=_allowed_attrs,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=CSS_SANITIZER,
    )


def sanitize_website(url):
    """Normaliza/valida o campo 'website' de comentários no servidor.
    Retorna None para entradas vazias, longas demais ou com esquema
    diferente de http/https (evita javascript:/data: em href)."""
    url = (url or "").strip()
    if not url or len(url) > 200:
        return None
    parsed = urlsplit(url)
    if parsed.scheme:
        # Já tem esquema (ex.: javascript:, data:, ftp:) — só aceita http/https.
        return url if parsed.scheme.lower() in ("http", "https") else None
    # Sem esquema (ex.: "exemplo.com") — normaliza para https.
    return "https://" + url


def normalize_base_url(url):
    return url.rstrip("/")


def extension_from_mime(mime):
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return mapping.get(mime.lower(), ".bin")


def ensure_bucket(supabase_url, service_key, bucket_name, timeout=30):
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
    }
    list_url = f"{supabase_url}/storage/v1/bucket"
    resp = requests.get(list_url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    buckets = resp.json()
    exists = any(
        b.get("id") == bucket_name or b.get("name") == bucket_name for b in buckets
    )
    if exists:
        return

    create_url = f"{supabase_url}/storage/v1/bucket"
    payload = {"id": bucket_name, "name": bucket_name, "public": True}
    resp = requests.post(create_url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code not in (200, 201, 409):
        resp.raise_for_status()


def upload_with_retry(
    supabase_url,
    service_key,
    bucket_name,
    remote_path,
    local_path,
    content_type,
    retries,
    backoff_seconds,
    timeout=120,
):
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
        "x-upsert": "true",
    }
    if content_type:
        headers["Content-Type"] = content_type

    upload_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{remote_path}"

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with open(local_path, "rb") as f:
                resp = requests.post(upload_url, headers=headers, data=f, timeout=timeout)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Upload falhou (status {resp.status_code}): {resp.text[:200]}"
                )
            return
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)

    raise RuntimeError(f"Falha no upload apos {retries} tentativas: {last_err}")


def is_public_supabase_url(url, public_base, bucket):
    if not url:
        return False
    parsed = urlsplit(url)
    if not parsed.scheme:
        return False
    public_prefix = f"{public_base}/storage/v1/object/public/{bucket}/"
    return url.startswith(public_prefix)


def replace_inline_images_with_supabase(content, post_id):
    if not content or "data:image" not in content:
        return content, 0

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_SERVICE_KEY sao obrigatorias para upload."
        )

    supabase_url = normalize_base_url(supabase_url)
    supabase_bucket = os.environ.get("SUPABASE_BUCKET", "post-images")
    public_url_base = normalize_base_url(
        os.environ.get("SUPABASE_PUBLIC_URL_BASE", supabase_url)
    )
    upload_retries = int(os.environ.get("UPLOAD_RETRIES", "5"))
    upload_backoff = float(os.environ.get("UPLOAD_BACKOFF_SECONDS", "2"))

    ensure_bucket(supabase_url, supabase_key, supabase_bucket)

    soup = BeautifulSoup(content, "html.parser")
    img_tags = soup.find_all("img")
    replaced = 0
    image_index = 0

    for tag in img_tags:
        src = tag.get("src")
        if not src or not src.lower().startswith("data:image/"):
            continue

        header, _, b64_data = src.partition(",")
        if not b64_data:
            continue

        try:
            mime = header.split(";")[0].split(":", 1)[1].strip()
            if mime.lower() == "image/svg+xml":
                raise RuntimeError(
                    "Upload de imagens SVG não é permitido por segurança."
                )
            raw = base64.b64decode(b64_data, validate=True)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Base64 invalido no post {post_id}: {exc}"
            ) from exc

        ext = extension_from_mime(mime)
        image_index += 1
        remote_path = f"posts/{post_id}/img_{image_index}{ext}"
        public_url = (
            f"{public_url_base}/storage/v1/object/public/{supabase_bucket}/{remote_path}"
        )

        if not is_public_supabase_url(src, public_url_base, supabase_bucket):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            try:
                tmp.write(raw)
                tmp.close()
                upload_with_retry(
                    supabase_url,
                    supabase_key,
                    supabase_bucket,
                    remote_path,
                    tmp.name,
                    mime,
                    upload_retries,
                    upload_backoff,
                )
            finally:
                try:
                    os.remove(tmp.name)
                except OSError:
                    pass

        tag["src"] = public_url
        replaced += 1

    return str(soup), replaced


def validate_supabase_env(app):
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        app.logger.warning(
            "Supabase upload desativado: variaveis ausentes: %s",
            ", ".join(missing),
        )
        return False

    app.logger.info("Supabase upload habilitado para posts.")
    return True


def log_upload_exception(exc, post_id):
    current_app.logger.exception(
        "Erro ao enviar imagens do post %s: %s", post_id, exc
    )
    return exc
def extract_image_and_excerpt(content):
    soup = BeautifulSoup(content, 'html.parser')
    image_tag = soup.find('img')
    image_src = image_tag['src'] if image_tag and image_tag.has_attr('src') else None
    
    if image_tag:
        image_tag.extract()
    
    for p in soup.find_all('p'):
        if any(text in p.get_text() for text in ["Photo by", "Imagem por"]):
            p.extract()
    
    text = soup.get_text()
    excerpt = ' '.join(text.split())[:150]
    
    return image_src, excerpt

def strip_leading_whitespace(html_content):
    if not html_content:
        return ''
    
    # Much simpler and safer pattern
    pattern = r'^(\s*(<p[^>]*>(\s|&nbsp;)*</p>|<br\s*/?>)\s*)+'
    return re.sub(pattern, '', html_content.strip(), count=1)
