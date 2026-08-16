#!/usr/bin/env bash
# =============================================================================
# testar_local.sh — Validação local das correções de segurança/qualidade
#
# Uso:
#   ./testar_local.sh            roda a suíte pytest + smoke tests automáticos
#   ./testar_local.sh --server   apenas sobe o servidor local (SQLite) e espera
#
# Seguro: usa um banco SQLite local (blog_local.db), NUNCA toca o Supabase.
# O servidor é derrubado ao final dos testes automáticos.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY="venv/Scripts/python.exe"
PORT="${TEST_PORT:-5001}"
BASE="http://127.0.0.1:${PORT}"
# Caminho ABSOLUTO em formato Windows (pwd -W -> C:/...): no Git Bash, o pwd
# retorna /c/... (formato MSYS) que o SQLite do Windows não abre, e um
# caminho relativo resolveria para a raiz do drive.
DB_FILE="$(pwd -W)/blog_local.db"
ADMIN_USER="admin"
ADMIN_PASS="admin123"   # somente para o ambiente de teste local

# Variáveis de ambiente do teste local (têm precedência sobre o .env do Supabase)
export SECRET_KEY="dev-local-key"
export DATABASE_URL="sqlite:///${DB_FILE}"
export SESSION_COOKIE_SECURE="false"
export TRUSTED_HOSTS="localhost,127.0.0.1"
export PORT="${PORT}"

# --- helpers ---------------------------------------------------------------

ok()   { echo "  ✔ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✘ $1"; FAIL=$((FAIL + 1)); }

get_csrf() { # <url> -> imprime o primeiro token csrf da página
  curl -s -b "$JAR" -c "$JAR" "$1" \
    | sed -n 's/.*name="csrf_token" value="\([^"]*\)".*/\1/p' | head -1 || true
}

# --- preparação ------------------------------------------------------------

echo "==> Preparando banco SQLite local (${DB_FILE})"

# Se já existe um servidor respondendo, recuse rodar contra ele (evita
# testar uma instância antiga e confundir os resultados).
if curl -s -o /dev/null "${BASE}/health" 2>/dev/null; then
  echo "ERRO: já existe um servidor em ${BASE}."
  echo "      Derrube-o (taskkill //F //IM python.exe) ou use TEST_PORT=5002 bash testar_local.sh"
  exit 1
fi

rm -f "$DB_FILE"
if [ -f "$DB_FILE" ]; then
  echo "ERRO: não foi possível remover ${DB_FILE} (arquivo em uso por outro processo)."
  exit 1
fi

"$PY" -c "
from app import create_app, db
from app.models import User, Post, Tag, Note, Comment

app = create_app()
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='${ADMIN_USER}').first():
        u = User(username='${ADMIN_USER}')
        u.set_password('${ADMIN_PASS}')
        db.session.add(u)

    if not Tag.query.filter_by(name='python').first():
        tag = Tag(name='python')
        post = Post(title='Primeiro post de teste',
                    content='<p>Conteudo de teste</p><a href=\"https://ok.com\">link</a>')
        post.tags.append(tag)
        nota = Note(content='**nota** de teste <script>alert(1)</script>')
        excluir = Post(title='Post para excluir', content='<p>vai sumir</p>')
        db.session.add_all([tag, post, nota, excluir])
        db.session.flush()
        db.session.add(Comment(post_id=excluir.id, name='Leitor', content='comentario'))
        db.session.commit()
        print('seed ok - post_id=%d nota_id=%d excluir_id=%d' % (post.id, nota.id, excluir.id))
    else:
        print('seed ok - dados ja existentes')
" > seed.out
cat seed.out

# Modo servidor: sobe e fica no foreground para teste manual
if [ "${1:-}" = "--server" ]; then
  echo ""
  echo "==> Servidor local em ${BASE} (admin: ${ADMIN_USER}/${ADMIN_PASS})"
  echo "    Ctrl+C para parar"
  "$PY" run.py
  exit 0
fi

# --- suíte automatizada ----------------------------------------------------

echo ""
echo "==> Suíte pytest (25 testes)"
"$PY" -m pytest -q

# --- servidor local --------------------------------------------------------

echo ""
echo "==> Subindo servidor local na porta ${PORT}"
"$PY" run.py > server.log 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  # Git Bash no Windows nem sempre propaga o kill ao processo subjacente;
  # o taskkill garante a morte real.
  taskkill //F //PID "$SERVER_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# aguarda o servidor responder
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "${BASE}/health"; then break; fi
  sleep 1
done
if ! curl -s -o /dev/null "${BASE}/health"; then
  echo "ERRO: servidor não subiu. Veja server.log:"; tail -20 server.log
  exit 1
fi

JAR="$(mktemp)"
PASS=0
FAIL=0

# --- smoke tests -----------------------------------------------------------

echo ""
echo "==> Smoke tests"

# 1. Health 200
code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/health")
[ "$code" = "200" ] && ok "health retorna 200" || fail "health retornou ${code}"

# 2. Home: sem FontAwesome, com SVG inline
body=$(curl -s "${BASE}/")
echo "$body" | grep -q "fontawesome" && fail "home ainda referencia fontawesome" \
  || ok "home sem fontawesome"
echo "$body" | grep -q "<svg" && ok "home com SVGs inline" || fail "home sem SVGs"

# 3. Sitemap inclui /notas e tags
sitemap=$(curl -s "${BASE}/sitemap.xml")
echo "$sitemap" | grep -q "/notas" && ok "sitemap inclui /notas" || fail "sitemap sem /notas"
echo "$sitemap" | grep -q "/tag/python" && ok "sitemap inclui tags" || fail "sitemap sem tags"

# 4. Post com JSON-LD
post_id=$(grep -o "post_id=[0-9]*" seed.out | cut -d= -f2)
curl -s "${BASE}/post/${post_id}" | grep -q "application/ld+json" \
  && ok "post com JSON-LD" || fail "post sem JSON-LD"

# 5. Host header inválido -> 400
code=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: evil.com" "${BASE}/")
[ "$code" = "400" ] && ok "Host evil.com -> 400" || fail "Host evil.com retornou ${code}"

# 6. XSS no website do comentário é bloqueado
csrf=$(get_csrf "${BASE}/post/${post_id}")
curl -s -b "$JAR" -c "$JAR" -o /dev/null \
  -d "name=XSS-Teste&website=javascript:alert(1)&content=oi&csrf_token=${csrf}" \
  "${BASE}/post/${post_id}"
"$PY" -c "
from app import create_app
from app.models import Comment
app = create_app()
with app.app_context():
    c = Comment.query.filter_by(name='XSS-Teste').one()
    assert c.website is None, 'website=%r' % c.website
" && ok "website javascript: bloqueado (armazenado como None)" \
  || fail "website javascript: não foi bloqueado"

# 7. Comentário longo é rejeitado (flash de erro)
LONGO=$(printf 'x%.0s' $(seq 1 1001))
csrf=$(get_csrf "${BASE}/post/${post_id}")
resp=$(curl -s -L -b "$JAR" -c "$JAR" \
  -d "name=Spam&content=${LONGO}&csrf_token=${csrf}" "${BASE}/post/${post_id}")
echo "$resp" | grep -q "Comentário muito longo" \
  && ok "comentário de 1001 chars rejeitado com mensagem" \
  || fail "comentário longo não foi rejeitado"

# 8. Markdown da nota é sanitizado (script escapado, não executável)
nota_id=$(grep -o "nota_id=[0-9]*" seed.out | cut -d= -f2)
curl -s "${BASE}/notas/${nota_id}" | grep -q "<script>alert" \
  && fail "script executável vazou na nota" \
  || ok "markdown da nota sanitizado"

# 9. Logout: GET retorna 405 e POST desloga
code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/admin/logout")
[ "$code" = "405" ] && ok "GET /admin/logout -> 405 (logout é POST)" \
  || fail "GET /admin/logout retornou ${code}"

# login com credenciais corretas (token da nova sessão para o logout)
csrf=$(get_csrf "${BASE}/admin/login")
curl -s -b "$JAR" -c "$JAR" -o /dev/null \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}&csrf_token=${csrf}" \
  "${BASE}/admin/login"
csrf=$(get_csrf "${BASE}/admin/")
code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" -c "$JAR" \
  -X POST -d "csrf_token=${csrf}" "${BASE}/admin/logout")
[ "$code" = "302" ] && ok "POST /admin/logout desloga (302)" || fail "logout POST retornou ${code}"

# 10. Apagar post com comentários não gera 500
excluir_id=$(grep -o "excluir_id=[0-9]*" seed.out | cut -d= -f2)
csrf=$(get_csrf "${BASE}/admin/login")
curl -s -b "$JAR" -c "$JAR" -o /dev/null \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}&csrf_token=${csrf}" \
  "${BASE}/admin/login"
csrf=$(get_csrf "${BASE}/admin/")
code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" -c "$JAR" \
  -d "csrf_token=${csrf}" "${BASE}/admin/delete_post/${excluir_id}")
[ "$code" = "302" ] && ok "delete de post com comentários -> 302 (sem 500)" \
  || fail "delete retornou ${code}"

# 11. Rate limit do login: 11 POSTs -> ao menos um 429
csrf=$(get_csrf "${BASE}/admin/login")
LIMITED=""
for _ in $(seq 1 11); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" -c "$JAR" \
    -d "username=x&password=y&csrf_token=${csrf}" "${BASE}/admin/login")
  if [ "$code" = "429" ]; then LIMITED="1"; break; fi
done
[ -n "$LIMITED" ] && ok "rate limit do login retorna 429" || fail "login nunca retornou 429"

# 12. Rate limit do comentário: POSTs seguidos -> ao menos um 429
csrf=$(get_csrf "${BASE}/post/${post_id}")
LIMITED=""
for _ in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" -c "$JAR" \
    -d "name=Ratelim&content=teste&csrf_token=${csrf}" "${BASE}/post/${post_id}")
  if [ "$code" = "429" ]; then LIMITED="1"; break; fi
done
[ -n "$LIMITED" ] && ok "rate limit de comentário retorna 429" || fail "comentário nunca retornou 429"

# --- fim -------------------------------------------------------------------

rm -f seed.out
echo ""
echo "================================================"
echo "Resultado: ${PASS} OK, ${FAIL} falhas"
if [ "$FAIL" -gt 0 ]; then
  echo "Detalhes do servidor em server.log"
  exit 1
else
  echo "TODOS OS TESTES LOCAIS PASSARAM"
  exit 0
fi
