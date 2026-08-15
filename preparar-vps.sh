#!/usr/bin/env bash
# =============================================================================
# preparar-vps.sh — prepara o ambiente da VPS para as correções de segurança
#
# Uso:
#   sudo bash preparar-vps.sh --check   diagnóstico SOMENTE-LEITURA (não altera nada)
#   sudo bash preparar-vps.sh           aplica as mudanças (com backup + auto-restauração)
#
# O que faz (com backup e auto-restauração em cada passo):
#   1. Cria o usuário ageublog (não-root) para o serviço
#   2. Ajusta permissão do .env (ageublog precisa ler as credenciais)
#   3. Adiciona SESSION_COOKIE_SECURE e TRUSTED_HOSTS ao .env (idempotente)
#   4. Atualiza o serviço systemd (User=ageublog, Group=www-data)
#      e reinicia — se falhar, restaura o serviço anterior
#   5. Nginx: adiciona location /static/ (cache) e substitui o CSP;
#      valida com `nginx -t` e, se inválido, restaura o backup
#   6. Verificação final: serviço ativo, health 200, estáticos com cache
#
# NÃO toca no banco (migração CASCADE é manual no Supabase) nem faz deploy.
# Único momento de "queda": ~2-5s no restart do serviço (igual a um deploy).
# Nginx é recarregado de forma graciosa (sem queda).
# =============================================================================
set -euo pipefail

APP_DIR=/var/www/app/app
SERVICE_FILE=/etc/systemd/system/ageu.service
DOMAIN=ageu.blog
NOW=$(date +%s)
BACKUP_DIR="$APP_DIR/.backup-vps-$NOW"

C_GREEN='\033[1;32m'; C_BLUE='\033[1;34m'; C_YELLOW='\033[1;33m'; C_RED='\033[1;31m'; C_END='\033[0m'
log()  { echo -e "${C_GREEN}[OK]${C_END}   $1"; }
info() { echo -e "${C_BLUE}[..]${C_END}   $1"; }
warn() { echo -e "${C_YELLOW}[!!]${C_END}   $1"; }
die()  { echo -e "${C_RED}[ERRO]${C_END}  $1"; exit 1; }

# v <nome> <comando...> — roda o comando em contexto condicional (imune ao
# set -e) e reporta ✔/✘ sem abortar.
v() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo -e "  ${C_GREEN}✔${C_END} $name"; PASS=$((PASS+1))
  else
    echo -e "  ${C_RED}✘${C_END} $name"; FAIL=$((FAIL+1))
  fi
}

find_nginx_conf() {
  for f in /etc/nginx/sites-available/ageu.blog /etc/nginx/sites-enabled/ageu.blog; do
    [ -f "$f" ] && { echo "$f"; return 0; }
  done
  # || true: sem match o grep retorna 1 e, com pipefail + set -e, derrubaria o script
  grep -rl "server_name.*${DOMAIN}" /etc/nginx/sites-available/ /etc/nginx/conf.d/ 2>/dev/null | head -1 || true
}

# ---------------------------------------------------------------------------
# MODO --check: diagnóstico somente-leitura (nada é alterado)
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--check" ]; then
  PASS=0; FAIL=0
  echo ""
  echo "================================================================"
  echo "  CHECK (somente leitura) — estado atual da VPS"
  echo "================================================================"

  v "executando como root"                 test "$(id -u)" = "0"
  v "app existe em $APP_DIR"               test -d "$APP_DIR"
  v "serviço systemd existe"               test -f "$SERVICE_FILE"
  v "nginx instalado"                      command -v nginx
  v "python3 instalado"                    command -v python3
  v "usuário ageublog existe"              id -u ageublog

  if [ -f "$APP_DIR/.env" ]; then
    ENVOWNER=$(stat -c %U "$APP_DIR/.env" 2>/dev/null || echo "?")
    v ".env de propriedade de ageublog (atual: $ENVOWNER)" \
      test "$ENVOWNER" = "ageublog"
    v "SESSION_COOKIE_SECURE=true no .env" grep -q "^SESSION_COOKIE_SECURE=true" "$APP_DIR/.env"
    v "TRUSTED_HOSTS com localhost no .env" grep -q "^TRUSTED_HOSTS=.*localhost" "$APP_DIR/.env"
  else
    echo -e "  ${C_RED}✘${C_END} .env não encontrado em $APP_DIR/.env"
    FAIL=$((FAIL+1))
  fi

  # Teste representativo: ageublog com Group=www-data, como o serviço roda.
  # (O teste por "others" dá falso positivo porque os dirs são ageu:www-data
  # com permissão de grupo vazia.)
  CAN_PROBE=0
  if command -v runuser >/dev/null 2>&1 \
     && [ "$(id -u)" = "0" ] \
     && id -u ageublog >/dev/null 2>&1; then
    CAN_PROBE=1
  fi
  if [ "$CAN_PROBE" = "1" ]; then
    v "ageublog:www-data consegue entrar no app (runuser)" \
      runuser -u ageublog -g www-data -- bash -c "cd '$APP_DIR'"
  else
    APP_MODE=$(stat -c %a "$APP_DIR" 2>/dev/null || echo "000")
    v "app dir legível por ageublog (mode atual: $APP_MODE)" \
      test "${APP_MODE: -1}" -ge 5
  fi

  if [ -f "$SERVICE_FILE" ]; then
    v "serviço roda como ageublog (User=)" grep -q "^User=ageublog" "$SERVICE_FILE"
    v "serviço com Group=www-data"         grep -q "^Group=www-data" "$SERVICE_FILE"
    if systemctl list-unit-files ageu.service >/dev/null 2>&1; then
      v "serviço ageu ativo"               systemctl is-active --quiet ageu
      SOCKOWNER=$(stat -c %U /run/ageu/ageu.sock 2>/dev/null || echo "não existe")
      v "socket de ageublog (atual: $SOCKOWNER)" test "$SOCKOWNER" = "ageublog"
      H=$(curl -s -o /dev/null -w "%{http_code}" --unix-socket /run/ageu/ageu.sock http://localhost/health || true)
      v "health via socket = 200 (atual: $H)" test "$H" = "200"
    else
      echo -e "  ${C_RED}✘${C_END} serviço ageu não carregado no systemd"
      FAIL=$((FAIL+1))
    fi
  fi

  PUB=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/health" || true)
  v "health público https://${DOMAIN}/health = 200 (atual: $PUB)" test "$PUB" = "200"

  NGINX_CONF=$(find_nginx_conf)
  if [ -n "$NGINX_CONF" ]; then
    info "Arquivo nginx encontrado: $NGINX_CONF"
    v "nginx com location /static/"        grep -q "location /static/" "$NGINX_CONF"
    if grep -q 'Content-Security-Policy.*darkvisitors' "$NGINX_CONF"; then
      echo -e "  ${C_GREEN}✔${C_END} CSP já é o novo (com darkvisitors)"
      PASS=$((PASS+1))
    else
      echo -e "  ${C_YELLOW}..${C_END} CSP atual não é o novo (será trocado)"
    fi
    v "nginx -t ok"                        nginx -t
  else
    echo -e "  ${C_RED}✘${C_END} config do nginx (server_name $DOMAIN) não encontrada"
    FAIL=$((FAIL+1))
  fi

  echo ""
  echo "  Resultado do check: $PASS prontos, $FAIL pendentes"
  if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "  Pendências: rode  sudo bash preparar-vps.sh  para aplicar."
    echo "  (o script é idempotente: só altera o que estiver faltando)"
    exit 1
  fi
  echo ""
  echo "  Tudo pronto! Falta apenas a migração CASCADE no Supabase e o git push."
  exit 0
fi

# ---------------------------------------------------------------------------
# Pré-condições (modo completo)
# ---------------------------------------------------------------------------
[ "$(id -u)" = "0" ] || die "rode como root:  sudo bash preparar-vps.sh"
[ -d "$APP_DIR" ]        || die "aplicação não encontrada em $APP_DIR"
[ -f "$SERVICE_FILE" ]   || die "serviço systemd não encontrado ($SERVICE_FILE)"
command -v nginx >/dev/null     || die "nginx não encontrado"
command -v python3 >/dev/null   || die "python3 não encontrado"

mkdir -p "$BACKUP_DIR"
echo ""
info "Backups serão gravados em: $BACKUP_DIR"
echo ""

# ---------------------------------------------------------------------------
# 1. Usuário ageublog
# ---------------------------------------------------------------------------
info "1/5 — Usuário de serviço ageublog (não-root)"
if id -u ageublog &>/dev/null; then
  log "ageublog já existe"
else
  useradd -r -s /usr/sbin/nologin ageublog
  log "ageublog criado"
fi

# ---------------------------------------------------------------------------
# 2. Permissão do .env
# ---------------------------------------------------------------------------
info "2/5 — Permissão do .env (ageublog precisa ler as credenciais)"
chown ageublog:ageublog "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"
log "chown ageublog:ageublog + chmod 600 em $APP_DIR/.env"
ls -l "$APP_DIR/.env"

# ---------------------------------------------------------------------------
# 3. Variáveis novas no .env (idempotente)
# ---------------------------------------------------------------------------
info "3/5 — SESSION_COOKIE_SECURE e TRUSTED_HOSTS no .env"
ENV_FILE="$APP_DIR/.env"

add_or_replace() { # <chave> <valor>
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    log "${key} atualizado"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
    log "${key} adicionado"
  fi
}

add_or_replace "SESSION_COOKIE_SECURE" "true"
# localhost/127.0.0.1 são OBRIGATÓRIOS: o health check do deploy acessa via
# socket com Host "localhost" — sem eles o pós-check do deploy falharia.
add_or_replace "TRUSTED_HOSTS" "ageu.blog,www.ageu.blog,localhost,127.0.0.1"

# ---------------------------------------------------------------------------
# 4. Serviço systemd (não-root) + restart com auto-restauração
# ---------------------------------------------------------------------------
info "4/5 — Serviço systemd como usuário não-root"
cp "$SERVICE_FILE" "$BACKUP_DIR/ageu.service.bak"

cat > "$SERVICE_FILE" << 'SERVICEEOF'
[Unit]
Description=Gunicorn - Flask App ageu.blog
After=network.target

[Service]
User=ageublog
# Group=www-data: o RuntimeDirectory fica ageublog:www-data 750 e o Nginx
# (www-data) consegue alcançar o socket. Com Group=ageublog daria 502.
Group=www-data
WorkingDirectory=/var/www/app/app
Environment="PATH=/var/www/app/app/venv/bin"
Environment="PYTHONDONTWRITEBYTECODE=1"
RuntimeDirectory=ageu
RuntimeDirectoryMode=750
ExecStart=/var/www/app/app/venv/bin/gunicorn run:app \
  --workers 2 \
  --bind unix:/run/ageu/ageu.sock \
  --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Causa real da falha anterior: o gunicorn (ageublog) não conseguiu entrar no
# WorkingDirectory (/var/www/app/app, de propriedade de outro usuário).
# Garante trânsito/leitura para TODOS na árvore do app (código é público;
# os segredos ficam no .env, que é re-trancado logo abaixo).
chmod o+x /var /var/www /var/www/app 2>/dev/null || true
# CRÍTICO: o serviço roda com Group=www-data. Os diretórios do app são
# ageu:www-data com permissão de GRUPO vazia (---) — por isso o processo
# ageublog:www-data cai nas permissões de grupo (não nas de "outros") e o
# chdir falha, mesmo com o+x em "outros".
chmod g+x /var/www/app 2>/dev/null || true
chmod -R o+rX "$APP_DIR" 2>/dev/null || true
chmod -R g+rX "$APP_DIR" 2>/dev/null || true
chown ageublog:ageublog "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"
log "permissões de acesso do app ajustadas para ageublog"

# Prova REPRESENTATIVA: ageublog com Group=www-data (exatamente como o serviço
# roda). O teste com o grupo padrão do ageublog dá falso positivo.
if command -v runuser >/dev/null 2>&1; then
  if runuser -u ageublog -g www-data -- bash -c "cd '$APP_DIR'" 2>/dev/null; then
    log "ageublog (Group=www-data) consegue entrar em $APP_DIR"
  else
    warn "ageublog:www-data NÃO consegue entrar em $APP_DIR — permissões de grupo bloqueiam:"
    ls -ld /var /var/www /var/www/app "$APP_DIR" 2>&1 || true
  fi
fi

rm -rf /run/ageu   # sobe limpo; /run é tmpfs (só o socket)
# Garante o diretório com o dono certo ANTES do restart, sem depender do
# RuntimeDirectory do systemd (que pode não criar/ajustar o owner).
install -d -o ageublog -g www-data -m 750 /run/ageu
systemctl daemon-reload
systemctl restart ageu
sleep 3

if systemctl is-active --quiet ageu; then
  log "serviço ageu ativo (User=ageublog)"
else
  warn "serviço falhou ao iniciar como ageublog — restaurando serviço anterior"
  echo "----- journal (últimas 25 linhas) -----"
  journalctl -u ageu -n 25 --no-pager || true
  echo "----- /run/ageu -----"
  ls -la /run/ageu/ 2>&1 || true
  echo "----- permissões do caminho (ls -ld) -----"
  ls -ld /var /var/www /var/www/app "$APP_DIR" 2>&1 || true
  cp "$BACKUP_DIR/ageu.service.bak" "$SERVICE_FILE"
  systemctl daemon-reload
  systemctl restart ageu
  die "serviço restaurado. Analise o journal acima antes de continuar."
fi

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --unix-socket /run/ageu/ageu.sock http://localhost/health || true)
[ "$HEALTH" = "200" ] || warn "health via socket retornou $HEALTH (esperado 200) — verifique journalctl -u ageu"
ls -la /run/ageu/ || true

# ---------------------------------------------------------------------------
# 5. Nginx: location /static/ + CSP (com backup e auto-restauração)
# ---------------------------------------------------------------------------
info "5/5 — Nginx: estáticos com cache + CSP alinhado"

NGINX_CONF=$(find_nginx_conf)
[ -n "$NGINX_CONF" ] || die "não encontrei o arquivo de config do Nginx (server_name ${DOMAIN})"
info "Arquivo Nginx: $NGINX_CONF"

cp "$NGINX_CONF" "$BACKUP_DIR/ageu.nginx.bak"

python3 - "$NGINX_CONF" << 'PYEOF'
import re, sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
orig = text
changes = []

static_block_lines = [
    "location /static/ {",
    "    alias /var/www/app/app/app/static/;",
    "    expires 30d;",
    "    add_header Cache-Control \"public, immutable\";",
    "    gzip_static on;",
    "}",
    "",
]

new_csp = (
    "add_header Content-Security-Policy \"default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://darkvisitors.com https://gc.zgo.at https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; font-src 'self' data:; "
    "connect-src 'self' https://ageu.goatcounter.com https://darkvisitors.com;\" always;"
)

def with_indent(lines, indent):
    return "".join(indent + line + "\n" for line in lines)

# 1) location /static/ (se ainda não existir)
if "location /static/" not in text:
    anchor = re.search(r"^(\s*)location = /feed\b", text, re.M)
    if not anchor:
        anchor = re.search(r"^(\s*)location /", text, re.M)
    if anchor:
        indent = anchor.group(1)
        text = text[:anchor.start()] + with_indent(static_block_lines, indent) + text[anchor.start():]
        changes.append("location /static/ inserido")
    else:
        print("ERRO: não achei âncora (location = /feed ou location /) para inserir os estáticos")
        sys.exit(2)
else:
    changes.append("location /static/ já existia")

# 2) CSP
csp_pat = re.compile(r"^[ \t]*add_header Content-Security-Policy .*;$", re.M)
if csp_pat.search(text):
    text = csp_pat.sub("    " + new_csp, text, count=1)
    changes.append("CSP substituída")
else:
    ref_pat = re.compile(r"^([ \t]*add_header Referrer-Policy .*)$", re.M)
    m = ref_pat.search(text)
    if m:
        indent = m.group(1)[:len(m.group(1)) - len(m.group(1).lstrip())]
        text = text[:m.end()] + "\n" + indent + new_csp + text[m.end():]
        changes.append("CSP inserida após Referrer-Policy")
    else:
        print("ERRO: não achei CSP nem Referrer-Policy para inserir o CSP novo")
        sys.exit(2)

if text != orig:
    open(path, "w", encoding="utf-8").write(text)
    for c in changes:
        print("OK: " + c)
else:
    print("OK: nginx já estava configurado")
PYEOF

if nginx -t; then
  systemctl reload nginx
  log "nginx -t ok e serviço recarregado (sem queda)"
else
  warn "nginx -t falhou — restaurando config anterior"
  cp "$BACKUP_DIR/ageu.nginx.bak" "$NGINX_CONF"
  nginx -t || warn "a config ORIGINAL também falhou — restaure manualmente: cp $BACKUP_DIR/ageu.nginx.bak $NGINX_CONF"
  die "nginx restaurado. Ajuste manualmente antes de continuar."
fi

# ---------------------------------------------------------------------------
# Verificação final
# ---------------------------------------------------------------------------
echo ""
echo "================================================================"
echo "  VERIFICAÇÃO FINAL"
echo "================================================================"
PASS=0
FAIL=0

v "serviço ageu ativo"                    systemctl is-active --quiet ageu
v "usuário ageublog existe"               id -u ageublog
if command -v runuser >/dev/null 2>&1; then
  v "ageublog:www-data entra no app (runuser)" \
    runuser -u ageublog -g www-data -- bash -c "cd '$APP_DIR'"
else
  APP_MODE=$(stat -c %a "$APP_DIR" 2>/dev/null || echo "000")
  v "app dir legível por ageublog (mode $APP_MODE)" test "${APP_MODE: -1}" -ge 5
fi
v ".env de propriedade de ageublog"       test "$(stat -c %U "$APP_DIR/.env" 2>/dev/null)" = "ageublog"
v "SESSION_COOKIE_SECURE=true no .env"    grep -q "^SESSION_COOKIE_SECURE=true" "$APP_DIR/.env"
v "TRUSTED_HOSTS com localhost no .env"   grep -q "^TRUSTED_HOSTS=.*localhost" "$APP_DIR/.env"
v "serviço roda como ageublog"            grep -q "^User=ageublog" "$SERVICE_FILE"
v "serviço com Group=www-data"            grep -q "^Group=www-data" "$SERVICE_FILE"

SOCKOWNER=$(stat -c %U /run/ageu/ageu.sock 2>/dev/null || echo "?")
v "socket é de ageublog (atual: $SOCKOWNER)" test "$SOCKOWNER" = "ageublog"

H=$(curl -s -o /dev/null -w "%{http_code}" --unix-socket /run/ageu/ageu.sock http://localhost/health || true)
v "health via socket = 200 (atual: $H)"   test "$H" = "200"

PUB=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/health" || true)
v "health público https://${DOMAIN}/health = 200 (atual: $PUB)" test "$PUB" = "200"

CACHE=$(curl -sI "https://${DOMAIN}/static/style.css" 2>/dev/null | grep -i "cache-control" || true)
if echo "$CACHE" | grep -qi immutable; then
  echo -e "  ${C_GREEN}✔${C_END} static/style.css com Cache-Control immutable ($CACHE)"
  PASS=$((PASS+1))
else
  echo -e "  ${C_RED}✘${C_END} static/style.css sem Cache-Control (atual: ${CACHE:-sem header})"
  FAIL=$((FAIL+1))
fi

v "nginx com location /static/"           grep -q "location /static/" "$NGINX_CONF"
v "nginx -t ok"                           nginx -t

echo ""
echo "  Backup das configs anteriores: $BACKUP_DIR"
echo "================================================================"
echo "  Resultado: $PASS OK, $FAIL falhas"
if [ "$FAIL" -gt 0 ]; then
  echo "  Revise os itens ✘ antes de fazer o deploy."
  exit 1
fi
echo "  Ambiente pronto! Agora:"
echo "    1) Faça a migração CASCADE no Supabase (SQL Editor)"
echo "    2) git push origin master (deploy automático)"
exit 0
