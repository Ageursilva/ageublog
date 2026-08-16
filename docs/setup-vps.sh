#!/bin/bash
# =============================================================================
# setup-vps.sh — Instalação completa do ageu.blog em nova VPS Ubuntu 24.04
# Uso: bash setup-vps.sh
# Tempo estimado: ~10 minutos
# =============================================================================

set -e  # Para imediatamente se qualquer comando falhar

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${YELLOW}➡️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo ""
echo "============================================="
echo "   Setup ageu.blog — VPS Ubuntu 24.04"
echo "============================================="
echo ""

# =============================================================================
# VARIÁVEIS — edite antes de rodar
# =============================================================================
GITHUB_REPO="git@github.com:Ageursilva/AgeuuBlog.git"
APP_DIR="/var/www/app/app"
DOMAIN="ageu.blog"
EMAIL_CERTBOT="SEU_EMAIL"
GITHUB_SSH_KEY=""  # Cole aqui a chave privada SSH do GitHub (deploy_key2) — entre aspas simples

# =============================================================================
# 1. Atualizar o sistema
# =============================================================================
info "Atualizando o sistema..."
apt update && apt upgrade -y
ok "Sistema atualizado"

# =============================================================================
# 2. Instalar dependências
# =============================================================================
info "Instalando dependências..."
apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    nginx \
    git \
    fail2ban \
    certbot \
    python3-certbot-nginx \
    curl \
    ufw
ok "Dependências instaladas"

# =============================================================================
# 3. Configurar firewall
# =============================================================================
info "Configurando firewall UFW..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80
ufw allow 443
ufw --force enable
ok "Firewall configurado"

# =============================================================================
# 4. Configurar SSH key para GitHub
# =============================================================================
info "Configurando SSH key para GitHub..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

if [ -z "$GITHUB_SSH_KEY" ]; then
    echo ""
    echo "⚠️  GITHUB_SSH_KEY não definida no script."
    echo "Gere uma nova chave SSH e adicione no GitHub:"
    echo ""
    echo "  ssh-keygen -t ed25519 -C 'deploy' -f ~/.ssh/deploy_key -N ''"
    echo "  cat ~/.ssh/deploy_key.pub  # adicione no GitHub → Settings → SSH Keys"
    echo "  cat ~/.ssh/deploy_key      # adicione nos Secrets do repo (VPS_SSH_KEY)"
    echo ""
    read -p "Pressione ENTER após configurar a chave SSH no GitHub..."
else
    echo "$GITHUB_SSH_KEY" > ~/.ssh/deploy_key
    chmod 600 ~/.ssh/deploy_key
    cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys 2>/dev/null || true
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/deploy_key
fi

# Aceitar GitHub como host conhecido
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
ok "SSH configurado"

# =============================================================================
# 5. Clonar o repositório
# =============================================================================
info "Clonando repositório..."
mkdir -p /var/www/app
cd /var/www/app

if [ -d "app" ]; then
    echo "Pasta app/ já existe — fazendo pull..."
    cd app && git pull origin master
else
    GIT_SSH_COMMAND="ssh -i ~/.ssh/deploy_key" git clone $GITHUB_REPO app
    cd app
fi
ok "Repositório clonado em $APP_DIR"

# =============================================================================
# 6. Criar e configurar venv Python
# =============================================================================
info "Criando ambiente virtual Python..."
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
ok "venv configurado e dependências instaladas"

# =============================================================================
# 7. Criar o .env
# =============================================================================
if [ ! -f "$APP_DIR/.env" ]; then
    info "Criando .env..."
    cat > $APP_DIR/.env << 'ENVEOF'
SECRET_KEY=TROQUE_POR_UMA_CHAVE_FORTE
DATABASE_URL=postgresql://postgres.PROJETO:SENHA@aws-0-us-west-2.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://PROJETO.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...
SUPABASE_BUCKET=post-images
SESSION_COOKIE_SECURE=true
# IMPORTANTE: manter localhost/127.0.0.1 — o health check do deploy acessa
# via socket com Host "localhost"; sem eles o deploy falharia no pós-check.
TRUSTED_HOSTS=ageu.blog,www.ageu.blog,localhost,127.0.0.1
ENVEOF
    chmod 600 $APP_DIR/.env
    echo ""
    echo "⚠️  Edite o .env com os valores reais antes de continuar:"
    echo "   nano $APP_DIR/.env"
    echo ""
    read -p "Pressione ENTER após editar o .env..."
else
    ok ".env já existe — mantendo"
fi

# =============================================================================
# 8. Diretório de runtime do socket
#    (criado automaticamente pelo systemd via RuntimeDirectory=ageu,
#     com posse transferida para o usuário ageublog)
# =============================================================================
info "Diretório do socket será gerenciado pelo systemd (RuntimeDirectory)"

# =============================================================================
# 9. Configurar systemd service (usuário dedicado, NÃO root)
# =============================================================================
info "Criando usuário de serviço ageublog (sem shell)..."
id -u ageublog &>/dev/null || useradd -r -s /usr/sbin/nologin ageublog
# O .env foi criado como root:root 600 — sem isso o app (ageublog) não consegue
# ler SECRET_KEY/DATABASE_URL e o serviço falha no boot.
chown ageublog:ageublog $APP_DIR/.env
chmod 600 $APP_DIR/.env

info "Configurando serviço systemd..."
cat > /etc/systemd/system/ageu.service << 'SERVICEEOF'
[Unit]
Description=Gunicorn - Flask App ageu.blog
After=network.target

[Service]
User=ageublog
# Group=www-data (não ageublog): o RuntimeDirectory fica ageublog:www-data 750,
# então o Nginx (www-data) consegue atravessar /run/ageu e alcançar o socket.
Group=www-data
WorkingDirectory=/var/www/app/app
Environment="PATH=/var/www/app/app/venv/bin"
# Evita tentativa de escrever __pycache__ em diretórios de propriedade do root
Environment="PYTHONDONTWRITEBYTECODE=1"
# Com User= definido, o systemd cria /run/ageu e transfere a posse para ageublog
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

systemctl daemon-reload
systemctl enable ageu
systemctl start ageu
ok "Serviço ageu configurado e iniciado"

# =============================================================================
# 10. Configurar Nginx
# =============================================================================
info "Configurando Nginx..."
cat > /etc/nginx/sites-available/ageu.blog << 'NGINXEOF'
# HTTP → HTTPS
server {
    listen 80;
    server_name ageu.blog www.ageu.blog;
    return 301 https://$host$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name ageu.blog www.ageu.blog;

    # Certificados Let's Encrypt (gerados pelo certbot)
    ssl_certificate /etc/letsencrypt/live/ageu.blog/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ageu.blog/privkey.pem;

    server_tokens off;
    client_max_body_size 10M;

    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    # CSP alinhado com os domínios realmente usados: DarkVisitors, GoatCounter
    # e Quill (admin, via jsdelivr). FontAwesome foi removido (SVGs inline).
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://darkvisitors.com https://gc.zgo.at https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://ageu.goatcounter.com https://darkvisitors.com;" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Estáticos: servidos direto pelo Nginx (cache + compressão), sem passar
    # pelo Gunicorn
    location /static/ {
        alias /var/www/app/app/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    # RSS Feed
    location = /feed {
        proxy_pass http://unix:/run/ageu/ageu.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # SOBRESCREVE o X-Forwarded-For com o IP real da conexão. NÃO usar
        # $proxy_add_x_forwarded_for: ele faz append e o ProxyFix do app lê o
        # PRIMEIRO valor (controlável pelo cliente) — permitindo spoofing de
        # IP e bypass do rate limit.
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        add_header Content-Type application/rss+xml;
    }

    # Proxy padrão
    location / {
        proxy_pass http://unix:/run/ageu/ageu.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # SOBRESCREVE o X-Forwarded-For com o IP real da conexão. NÃO usar
        # $proxy_add_x_forwarded_for: ele faz append e o ProxyFix do app lê o
        # PRIMEIRO valor (controlável pelo cliente) — permitindo spoofing de
        # IP e bypass do rate limit.
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/ageu.blog /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
ok "Nginx configurado"

# =============================================================================
# 11. SSL com Certbot
# =============================================================================
info "Gerando certificado SSL..."
echo ""
echo "⚠️  Para o Certbot funcionar, o DNS do domínio já deve apontar para o IP desta VPS."
echo ""
read -p "O DNS já está apontado para esta VPS? (s/n): " DNS_OK

if [ "$DNS_OK" = "s" ]; then
    certbot --nginx -d ageu.blog -d www.ageu.blog --email $EMAIL_CERTBOT --agree-tos --non-interactive
    systemctl reload nginx
    ok "SSL configurado"
else
    echo "⚠️  Aponte o DNS primeiro e depois rode:"
    echo "   certbot --nginx -d ageu.blog -d www.ageu.blog --email $EMAIL_CERTBOT --agree-tos"
fi

# =============================================================================
# 12. Configurar Fail2ban
# =============================================================================
info "Configurando Fail2ban..."
cat > /etc/fail2ban/jail.local << 'FAIL2BANEOF'
[DEFAULT]
action = %(action_)s
         telegram

[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 86400
findtime = 600
FAIL2BANEOF

cat > /etc/fail2ban/action.d/telegram.conf << 'TELEGRAMEOF'
[Definition]
actionban = /etc/fail2ban/notify-telegram.sh <ip>
actionunban =
TELEGRAMEOF

cat > /etc/fail2ban/notify-telegram.sh << 'SCRIPTEOF'
#!/bin/bash
TOKEN="COLOQUE_O_TOKEN_DO_BOT_AQUI"
CHAT_ID="SEU_CHAT_ID"
IP="$1"
MESSAGE="🚨 *Fail2ban ageu.blog*
IP banido: \`$IP\`
Data: $(date '+%d/%m/%Y %H:%M:%S')"

curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
  -d chat_id="$CHAT_ID" \
  -d text="$MESSAGE" \
  -d parse_mode="Markdown" > /dev/null
SCRIPTEOF

chmod +x /etc/fail2ban/notify-telegram.sh
systemctl enable fail2ban
systemctl restart fail2ban
echo ""
echo "⚠️  Edite o token do Telegram no script:"
echo "   nano /etc/fail2ban/notify-telegram.sh"
echo ""
ok "Fail2ban configurado"

# =============================================================================
# 13. Configurar SSH key para GitHub Actions (deploy automático)
# =============================================================================
info "Gerando SSH key para GitHub Actions..."
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key_actions -N ""
cat ~/.ssh/deploy_key_actions.pub >> ~/.ssh/authorized_keys
echo ""
echo "⚠️  Adicione a chave privada abaixo nos Secrets do GitHub (VPS_SSH_KEY):"
echo ""
cat ~/.ssh/deploy_key_actions
echo ""
read -p "Pressione ENTER após adicionar o secret no GitHub..."
ok "SSH key para Actions gerada"

# =============================================================================
# 14. Status final
# =============================================================================
echo ""
echo "============================================="
echo "   ✅ Setup concluído!"
echo "============================================="
echo ""
systemctl status ageu --no-pager | head -5
echo ""
echo "Checklist pós-instalação:"
echo "  [ ] Editar .env com valores reais: nano $APP_DIR/.env"
echo "  [ ] Editar token Telegram: nano /etc/fail2ban/notify-telegram.sh"
echo "  [ ] Adicionar VPS_SSH_KEY nos Secrets do GitHub"
echo "  [ ] Apontar DNS para o IP desta VPS"
echo "  [ ] Rodar certbot se ainda não fez"
echo "  [ ] Testar https://ageu.blog/health"
echo ""