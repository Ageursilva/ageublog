# ageu.blog — Documentação Completa

> Última atualização: 27/06/2026  
> Servidor: VPS Ubuntu 24.04 — IP SEU_IP  
> Domínio: ageu.blog

---

## Stack

| Componente     | Tecnologia            | Versão    |
| -------------- | --------------------- | --------- |
| Linguagem      | Python                | 3.12.3    |
| Framework      | Flask                 | 3.1.3     |
| Servidor WSGI  | Gunicorn              | 26.0.0    |
| Proxy reverso  | Nginx                 | 1.24.0    |
| Banco de dados | Supabase (PostgreSQL) | —         |
| Storage        | Supabase Storage      | —         |
| ORM            | SQLAlchemy            | 2.0.51    |
| Repositório    | GitHub (privado)      | AgeuuBlog |
| Deploy         | GitHub Actions        | —         |

---

## Estrutura de pastas na VPS

```
/var/www/app/app/                    ← raiz do projeto e do .git
  run.py                             ← entry point do Gunicorn (run:app)
  requirements.txt
  .env                               ← chmod 600, nunca vai ao git
  .env.example                       ← template sem valores reais
  .github/
    workflows/
      deploy.yml                     ← GitHub Actions
  app/                               ← módulo Flask (pacote Python)
    __init__.py                      ← create_app(), registra blueprints
    views.py                         ← rotas públicas (Blueprint: main)
    admin.py                         ← rotas admin (Blueprint: admin)
    models.py                        ← modelos SQLAlchemy (Post, User, Comment)
    config.py                        ← configurações Flask (o correto)
    utils.py                         ← funções auxiliares
    static/
      style.css
      script.js
      favicon.ico
      logo.png
      robots.txt
    templates/
      base.html                      ← usado por radar.html, search_results.html e radar_placeholder.html
      index.html                     ← home
      post.html                      ← post individual + comentários
      about.html
      login.html
      admin.html                     ← painel admin completo
      admin_comments.html            ← moderação de comentários
      404.html
      500.html
      feed.xml
      sitemap.xml
      radar.html
      radar_placeholder.html
      search_results.html
      google4f797673843906aa.html    ← verificação Google Search Console
  docs/
    setup.md                         ← este arquivo
    setup-vps.sh                     ← script de instalação em nova VPS
  venv/                              ← ambiente virtual Python local, fora do git
```

**Atenção:** a maioria dos templates é um HTML completo independente; apenas `radar.html`, `search_results.html` e `radar_placeholder.html` usam `{% extends 'base.html' %}`. Ícones são SVG inline (`_icons.html`) — o FontAwesome foi removido.

---

## Serviços e configurações

### Gunicorn (systemd)

Arquivo: `/etc/systemd/system/ageu.service`

```ini
[Unit]
Description=Gunicorn - Flask App ageu.blog
After=network.target

[Service]
User=ageublog
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
```

Comandos úteis:
```bash
systemctl status ageu          # ver status
systemctl restart ageu         # reiniciar
systemctl stop ageu            # parar
journalctl -u ageu -n 50       # ver logs
journalctl -u ageu -f          # logs em tempo real
```

### Nginx

Arquivo: `/etc/nginx/sites-available/ageu.blog`

Configuração completa:
- HTTP → HTTPS redirect
- SSL via Let's Encrypt (Certbot)
- Headers de segurança completos
- Proxy para socket Unix do Gunicorn
- Location especial para `/feed` (Content-Type RSS)
- Location especial para `/sitemap.xml` (sem CSP)

Comandos úteis:
```bash
nginx -t                        # testar configuração
systemctl reload nginx          # recarregar sem downtime
systemctl restart nginx         # reiniciar completo
cat /var/log/nginx/error.log    # logs de erro
```

### Fail2ban

Arquivo: `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
action = %(action_)s
         telegram

[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 86400
findtime = 600
```

Script de alerta: `/etc/fail2ban/notify-telegram.sh`
- Token do bot: salvo no script
- Chat ID: SEU_CHAT_ID

Comandos úteis:
```bash
fail2ban-client status sshd          # ver IPs banidos
fail2ban-client unban IP             # desbanir IP
tail -f /var/log/fail2ban.log        # log em tempo real
systemctl restart fail2ban           # reiniciar
```

---

## Variáveis de ambiente (.env)

Arquivo na VPS: `/var/www/app/app/.env` (chmod 600)

```env
SECRET_KEY=<chave forte 64 chars>
DATABASE_URL=postgresql://postgres.PROJETO:SENHA@aws-0-us-west-2.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://PROJETO.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...
SUPABASE_BUCKET=post-images
```

**Atenção:** o `DATABASE_URL` usa o **Session Pooler do Supabase (porta 6543)** — conexões diretas usam IPv6 e não funcionam em redes IPv4-only.

Para rodar local no Windows, o `.env` é idêntico. O `.gitignore` garante que nunca vai ao GitHub.

---

## Banco de dados (Supabase)

### Tabelas

**post**
| Campo         | Tipo      | Descrição                         |
| ------------- | --------- | --------------------------------- |
| id            | SERIAL PK | ID do post                        |
| title         | VARCHAR   | Título                            |
| content       | TEXT      | Conteúdo HTML (gerado pelo Quill) |
| created_at    | TIMESTAMP | Data de criação                   |
| category      | VARCHAR   | Categoria (opcional)              |
| status        | VARCHAR   | Status                            |
| published_at  | TIMESTAMP | Data de publicação                |
| scheduled_for | TIMESTAMP | Agendamento                       |

**comment**
| Campo      | Tipo         | Descrição                                |
| ---------- | ------------ | ---------------------------------------- |
| id         | SERIAL PK    | ID do comentário                         |
| post_id    | INTEGER FK   | Referência ao post                       |
| parent_id  | INTEGER FK   | Referência ao comentário pai (respostas) |
| name       | VARCHAR(100) | Nome do autor                            |
| website    | VARCHAR(200) | Site do autor (opcional)                 |
| content    | TEXT         | Conteúdo do comentário                   |
| is_author  | BOOLEAN      | TRUE se comentou logado como admin       |
| seen       | BOOLEAN      | TRUE se admin já viu                     |
| created_at | TIMESTAMP    | Data de criação                          |

**user**
| Campo         | Tipo         | Descrição              |
| ------------- | ------------ | ---------------------- |
| id            | SERIAL PK    | ID do usuário          |
| username      | VARCHAR      | Nome de usuário        |
| password_hash | VARCHAR(128) | Hash da senha (pbkdf2) |

### RLS (Row Level Security)
Todas as tabelas têm RLS habilitado no Supabase.

### Storage
Bucket: `post-images` — imagens dos posts são enviadas para o Supabase Storage automaticamente ao publicar.

---

## Deploy automático

Arquivo: `.github/workflows/deploy.yml`

```yaml
name: Deploy VPS
on:
  push:
    branches: [master]
jobs:
  test:                      # roda os 25 testes; se falhar, não deploya
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: SSH deploy
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /var/www/app/app
            PREV_COMMIT=$(git rev-parse HEAD)
            git pull origin master
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            systemctl restart ageu
            sleep 5
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
              --unix-socket /run/ageu/ageu.sock http://localhost/health)
            if [ "$HTTP_STATUS" != "200" ]; then
              echo "Deploy falhou! Health check retornou $HTTP_STATUS"
              git checkout master
              git reset --hard $PREV_COMMIT
              pip install -r requirements.txt --quiet
              systemctl restart ageu
              exit 1
            fi
```

**Secrets no GitHub (Settings → Secrets → Actions):**

| Secret        | Valor                                            |
| ------------- | ------------------------------------------------ |
| `VPS_HOST`    | `SEU_IP`                                 |
| `VPS_USER`    | `root`                                           |
| `VPS_SSH_KEY` | Conteúdo de `~/.ssh/deploy_key2` (chave privada) |

A chave pública está em `~/.ssh/authorized_keys` na VPS.

**Fluxo completo:**
```
Edita no VSCode (Windows)
  ↓ python run.py → testa em localhost:5000
  ↓ git add . && git commit -m "..." && git push origin master
  ↓ GitHub Actions SSHa na VPS (~20 segundos)
  ↓ git pull + pip install + systemctl restart
  ↓ Blog atualizado em ageu.blog
```

---

## Setup local no Windows

```bash
# 1. Clonar
git clone git@github.com:Ageursilva/AgeuuBlog.git
cd AgeuuBlog

# 2. Criar venv
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar .env local (mesmos valores da VPS)
# DATABASE_URL usa pooler Supabase porta 6543

# 5. Rodar
python run.py
# Acessa http://localhost:5000
```

**Atenção no Windows:** não instalar PostgreSQL localmente — conflita com o psycopg2 e causa UnicodeDecodeError.

---

## Rotas do blog

### Públicas

| Rota               | Descrição                  |
| ------------------ | -------------------------- |
| `GET /`            | Home com paginação         |
| `GET /post/<id>`   | Post individual            |
| `POST /post/<id>`  | Enviar comentário          |
| `GET /about`       | Página sobre               |
| `GET /radar`       | Radar Cultural             |
| `GET /search`      | Busca de posts             |
| `GET /feed`        | RSS feed (application/xml) |
| `GET /sitemap.xml` | Sitemap para SEO           |
| `GET /robots.txt`  | Robots                     |
| `GET /health`      | Health check (JSON)        |

### Admin (requer login)

| Rota                                  | Descrição                      |
| ------------------------------------- | ------------------------------ |
| `GET/POST /admin/login`               | Login (rate limit: 10/min)     |
| `POST /admin/logout`                  | Logout (POST — anti CSRF)      |
| `GET /admin/`                         | Painel principal com busca     |
| `GET/POST /admin/create_post`         | Criar post                     |
| `GET/POST /admin/edit_post/<id>`      | Editar post                    |
| `POST /admin/delete_post/<id>`        | Excluir post                   |
| `GET /admin/comments`                 | Moderação de comentários       |
| `POST /admin/comments/delete/<id>`    | Excluir comentário             |
| `POST /admin/comments/seen/<post_id>` | Marcar comentários como vistos |

---

## Verificar status na VPS

```bash
# Último commit na VPS
git log --oneline -5

# Está sincronizado com o GitHub?
git fetch origin && git status

# Gunicorn está rodando?
systemctl status ageu

# Nginx está rodando?
systemctl status nginx

# Fail2ban está rodando?
systemctl status fail2ban
fail2ban-client status sshd

# Blog respondendo?
curl -I https://ageu.blog
curl -s https://ageu.blog/health
```

---

## Segurança

### Status atual

| Item                                         | Status                                   |
| -------------------------------------------- | ---------------------------------------- |
| SECRET_KEY forte no .env                     | ✅                                        |
| .env com chmod 600                           | ✅                                        |
| .env fora do git (.gitignore)                | ✅                                        |
| RLS habilitado no Supabase                   | ✅                                        |
| Rate limiting no /admin/login (10/min)       | ✅                                        |
| CSRF protegido (flask-wtf)                   | ✅                                        |
| XSS protegido (bleach)                       | ✅                                        |
| .git não exposto publicamente                | ✅                                        |
| Headers de segurança no Nginx                | ✅                                        |
| Content-Security-Policy                      | ✅                                        |
| Senha admin forte (pbkdf2)                   | ✅                                        |
| SSH key dedicada para GitHub Actions         | ✅                                        |
| Fail2ban ativo (bane após 3 tentativas, 24h) | ✅                                        |
| Alertas de ban via Telegram                  | ✅                                        |
| SSH por chave (sem senha)                    | 🟡 quando migrar para VPS com console VNC |
| Expiração de sessão do admin                 | 🟡 pendente                               |

### Headers de segurança (Nginx)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: (ver nginx config)
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### CSP completo (fonte da verdade: `docs/setup-vps.sh`)

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://darkvisitors.com https://gc.zgo.at https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
font-src 'self' data:;
img-src 'self' data: https:;
connect-src 'self' https://ageu.goatcounter.com https://darkvisitors.com;
```

> FontAwesome foi removido (SVGs inline em `_icons.html`). O Quill (admin) é
> carregado de `cdn.jsdelivr.net`. `frame-src` não é necessário (sem iframes).

### Nginx — estáticos com cache

O `location /static/` é servido direto pelo Nginx (não passa pelo Gunicorn):

```nginx
location /static/ {
    alias /var/www/app/app/app/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    gzip_static on;
}
```

### Variáveis de ambiente adicionais (`.env`)

```bash
SESSION_COOKIE_SECURE=true
# localhost/127.0.0.1 OBRIGATÓRIOS: o health check do deploy acessa via socket
# com Host "localhost" — sem eles o pós-check do deploy falharia.
TRUSTED_HOSTS=ageu.blog,www.ageu.blog,localhost,127.0.0.1
```

### Permissões de arquivos importantes

```bash
chmod 600 /var/www/app/app/.env
chmod 600 ~/.ssh/deploy_key2
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod +x /etc/fail2ban/notify-telegram.sh
```

---

## Monitoramento

### UptimeRobot
- Monitora `https://ageu.blog/health`
- Verifica keyword `"ok"` no JSON
- Alerta por email se cair

### Health check (`/health`)
Retorna:
```json
{
  "status": "ok",
  "database": "ok",
  "version": "1.0"
}
```

### Google Search Console
- Verificado via metatag no `index.html`
- Sitemap submetido: `https://ageu.blog/sitemap.xml`

### GoatCounter
- Analytics em `https://ageu.goatcounter.com`
- Script carregado via `//gc.zgo.at/count.js`
- Sem cookies, respeita privacidade

---

## Debug — problemas comuns

### Blog não sobe após deploy

```bash
# Ver logs do Gunicorn
journalctl -u ageu -n 50

# Ver se o socket existe
ls -la /run/ageu/ageu.sock

# Reiniciar manualmente
systemctl restart ageu
```

### Conflito no git pull (mudanças locais na VPS)

```bash
git stash
git pull origin master
systemctl restart ageu
```

**Atenção:** nunca editar arquivos diretamente na VPS. Sempre editar no Windows e subir via git push.

### Deploy não atualizou os templates

```bash
# Ver qual commit está na VPS
git log --oneline -3

# Comparar com GitHub
git fetch origin
git status

# Se estiver desatualizado
git pull origin master
systemctl restart ageu
```

### Erro 500 no blog

```bash
# Ver logs detalhados
journalctl -u ageu -n 100

# Testar o app diretamente (sem Nginx)
curl -s http://localhost:5000/health
```

### Nginx não recarrega

```bash
# Testar configuração primeiro
nginx -t

# Se ok, recarregar
systemctl reload nginx
```

### Fail2ban baniu seu próprio IP

```bash
# Ver seu IP
curl ifconfig.me

# Desbanir
fail2ban-client unban SEU_IP
```

### Banco de dados não conecta

```bash
# Testar conexão
curl -s https://ageu.blog/health

# Se database: error, verificar:
# 1. Supabase está online? supabase.com/dashboard
# 2. DATABASE_URL está correta no .env?
cat /var/www/app/app/.env | grep DATABASE_URL
```

---

## Backup

### Script de backup das configs

Arquivo: `/root/backup-config.sh`

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/root/backups/$DATE"
mkdir -p $BACKUP_DIR

cp /etc/nginx/sites-available/ageu.blog $BACKUP_DIR/nginx-ageu.blog
cp /etc/systemd/system/ageu.service $BACKUP_DIR/ageu.service
cp /etc/fail2ban/jail.local $BACKUP_DIR/jail.local
cp /etc/fail2ban/action.d/telegram.conf $BACKUP_DIR/telegram.conf
cp /etc/fail2ban/notify-telegram.sh $BACKUP_DIR/notify-telegram.sh
cp /var/www/app/app/.env $BACKUP_DIR/.env

echo "Backup concluído em $BACKUP_DIR"
```

### O que está seguro no GitHub

- Todo o código fonte
- Templates
- CSS, JS
- requirements.txt
- GitHub Actions workflow

### O que NÃO está no GitHub (manter backup manual)

- `.env` (senhas, tokens)
- Token do Telegram (`/etc/fail2ban/notify-telegram.sh`)
- Chaves SSH (`~/.ssh/deploy_key2`)
- Configuração do Nginx (`/etc/nginx/sites-available/ageu.blog`)

---

## Reinstalar em nova VPS

Script completo em: `docs/setup-vps.sh`

```bash
# Em nova VPS Ubuntu 24.04
bash setup-vps.sh
```

O script faz tudo automaticamente. Após rodar, preencher manualmente:
1. `/var/www/app/app/.env` com os valores reais
2. `/etc/fail2ban/notify-telegram.sh` com o token do Telegram
3. Adicionar `VPS_SSH_KEY` nos Secrets do GitHub

---

## Scripts externos usados

| Serviço      | URL                 | Finalidade                   |
| ------------ | ------------------- | ---------------------------- |
| SVG inline   | — (local)           | Ícones (`_icons.html`)       |
| DarkVisitors | darkvisitors.com    | Proteção contra bots         |
| GoatCounter  | gc.zgo.at           | Analytics                    |
| QuillJS      | cdn.jsdelivr.net    | Editor rich text (admin)     |
| Utterances   | utteranc.es         | (removido — sistema próprio) |

---

## Pendente / backlog

- [ ] Expiração de sessão do admin (`PERMANENT_SESSION_LIFETIME`)
- [ ] Backup automático via cron
- [ ] Formatação Quill nos posts (carregar CSS do Quill no `post.html`)
- [ ] SSH por chave sem senha (requer VPS com console VNC)
- [ ] Atualizar repo open source (ageublog) com as novas features
- [ ] Crescimento orgânico — estratégia de conteúdo SEO
