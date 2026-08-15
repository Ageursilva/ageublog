# ageu.blog — Arquitetura e Funcionamento Completo

> Documento técnico completo sobre como o blog funciona, cada componente, fluxos de dados e decisões de arquitetura.
> Última atualização: 01/07/2026

---

## Visão Geral

```
Usuário (browser)
    ↓ HTTPS
Nginx (proxy reverso + SSL + headers de segurança)
    ↓ Unix socket
Gunicorn (servidor WSGI, 2 workers)
    ↓ WSGI
Flask (framework Python)
    ↓ SQLAlchemy ORM
Supabase (PostgreSQL na nuvem)
    ↓ Supabase Storage
Imagens dos posts (CDN)
```

---

## Infraestrutura

### VPS
- Provedor: MINIVPS
- IP: SEU_IP
- OS: Ubuntu 24.04 LTS
- RAM: 1GB, 1 vCPU, 10GB disco
- **Limitação importante:** sem console VNC/de emergência — só Reiniciar/Desligar/Reinstalar via painel

### Domínio
- ageu.blog (apontado para o IP da VPS via DNS)
- SSL via Let's Encrypt (Certbot), renovação automática

### Banco de dados
- Supabase (PostgreSQL gerenciado na nuvem)
- Região: us-west-2
- Conexão via Session Pooler (porta 6543) — NÃO via conexão direta (porta 5432 usa IPv6, quebra em redes IPv4-only)
- Storage para imagens dos posts no mesmo projeto Supabase

---

## Stack técnica completa

| Componente       | Tecnologia            | Versão    |
| ---------------- | --------------------- | --------- |
| Linguagem        | Python                | 3.12.3    |
| Framework web    | Flask                 | 3.1.3     |
| Servidor WSGI    | Gunicorn              | 25.0.3    |
| Proxy reverso    | Nginx                 | 1.24.0    |
| ORM              | SQLAlchemy            | 2.0.51    |
| Banco de dados   | Supabase (PostgreSQL) | —         |
| Sanitização HTML | Bleach                | 6.4.0     |
| Proteção CSRF    | Flask-WTF             | 1.3.0     |
| Rate limiting    | Flask-Limiter         | 4.1.1     |
| Editor rich text | QuillJS               | 1.3.6     |
| Analytics        | GoatCounter           | —         |
| Ícones           | SVG inline (_icons.html) | —       |
| Firewall         | UFW                   | —         |
| Proteção SSH     | Fail2ban              | 1.0.2     |
| Reporte de IPs   | AbuseIPDB             | API v2    |
| Deploy           | GitHub Actions        | —         |
| Repositório      | GitHub (privado)      | AgeuuBlog |

---

## Estrutura de pastas completa

```
/var/www/app/app/                        ← raiz do projeto e do .git
│
├── .git/                                ← repositório git
├── .github/
│   └── workflows/
│       └── deploy.yml                   ← GitHub Actions (CI/CD)
│
├── app/                                 ← módulo Flask (pacote Python)
│   ├── __init__.py                      ← factory pattern: create_app()
│   ├── views.py                         ← Blueprint 'main' (rotas públicas)
│   ├── admin.py                         ← Blueprint 'admin' (rotas /admin/*)
│   ├── models.py                        ← modelos SQLAlchemy
│   ├── config.py                        ← configurações Flask
│   ├── utils.py                         ← funções auxiliares
│   │
│   ├── static/                          ← arquivos estáticos
│   │   ├── style.css
│   │   ├── script.js
│   │   ├── favicon.ico
│   │   ├── logo.png
│   │   └── robots.txt
│   │
│   └── templates/                       ← templates Jinja2
│       ├── index.html                   ← home
│       ├── post.html                    ← post individual + comentários
│       ├── about.html                   ← página sobre
│       ├── login.html                   ← login admin
│       ├── admin.html                   ← painel admin completo
│       ├── admin_comments.html          ← moderação de comentários
│       ├── admin_tags.html              ← gerenciamento de tags
│       ├── radar.html                   ← radar cultural
│       ├── radar_placeholder.html       ← radar sem conteúdo
│       ├── search_results.html          ← resultados de busca
│       ├── tag.html                     ← posts por tag
│       ├── 404.html
│       ├── 500.html
│       ├── feed.xml                     ← RSS feed
│       ├── sitemap.xml                  ← sitemap para SEO
│       └── _icons.html                  ← SVG inline (rss, busca, linkedin, github)
│
├── docs/
│   ├── setup.md                         ← documentação técnica
│   └── setup-vps.sh                     ← script de instalação em nova VPS
│
├── run.py                               ← entry point
├── .env                                 ← variáveis de ambiente (chmod 600)
├── .env.example                         ← template sem valores reais
├── .gitignore
└── requirements.txt
```

**Regra:** a maioria dos templates é HTML completo e independente (`base.html` foi mantido e é usado por `radar.html`, `search_results.html` e `radar_placeholder.html`). Os ícones são SVG inline via `_icons.html` (sem FontAwesome/CDN).

---

## Como o Flask está organizado

### Factory Pattern (`app/__init__.py`)

```python
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)      # SQLAlchemy
    csrf.init_app(app)    # Flask-WTF
    limiter.init_app(app) # Flask-Limiter
    
    # Registra blueprints
    from .views import main
    from .admin import admin
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    return app
```

### Blueprints

**Blueprint `main`** — rotas públicas do blog:
- `/` — home com paginação
- `/post/<id>` — post individual (GET + POST para comentários)
- `/about` — sobre
- `/radar` — radar cultural
- `/search` — busca de posts
- `/tag/<name>` — posts por tag
- `/feed` — RSS (Content-Type: application/xml)
- `/sitemap.xml` — sitemap SEO
- `/robots.txt` — robots
- `/health` — health check JSON

**Blueprint `admin`** — rotas protegidas por login:
- `/admin/login` — autenticação (rate limit: 10/min)
- `/admin/logout` — encerrar sessão
- `/admin/` — painel principal com busca
- `/admin/create_post` — criar post
- `/admin/edit_post/<id>` — editar post
- `/admin/delete_post/<id>` — excluir post
- `/admin/tags` — gerenciar tags
- `/admin/tags/delete/<id>` — excluir tag
- `/admin/comments` — moderação de comentários
- `/admin/comments/delete/<id>` — excluir comentário
- `/admin/comments/seen/<post_id>` — marcar comentários como vistos

---

## Banco de dados

### Tabelas e relacionamentos

```
post (1) ←──── (N) post_tags (N) ────→ (1) tag
  ↓ (1)
comment (N)
  ↓ (1) [self-referencing para respostas]
comment (N)

user (standalone — só admin)
```

### Esquema completo

**post**
```sql
id          SERIAL PRIMARY KEY
title       VARCHAR
content     TEXT              -- HTML gerado pelo QuillJS
created_at  TIMESTAMP
```

**tag**
```sql
id    SERIAL PRIMARY KEY
name  VARCHAR(100) UNIQUE
```

**post_tags** (many-to-many)
```sql
post_id  INTEGER FK → post.id
tag_id   INTEGER FK → tag.id
```

**comment**
```sql
id         SERIAL PRIMARY KEY
post_id    INTEGER FK → post.id (CASCADE DELETE)
parent_id  INTEGER FK → comment.id (nullable — respostas)
name       VARCHAR(100)
website    VARCHAR(200)
content    TEXT
is_author  BOOLEAN DEFAULT FALSE  -- TRUE quando admin comenta logado
seen       BOOLEAN DEFAULT FALSE  -- controle de moderação
created_at TIMESTAMP
```

**user**
```sql
id             SERIAL PRIMARY KEY
username       VARCHAR
password_hash  VARCHAR(128)  -- pbkdf2 via werkzeug
```

### RLS (Row Level Security)
Todas as tabelas têm RLS habilitado no Supabase. Políticas configuradas para leitura pública onde necessário e escrita via service_role.

### Conexão com o banco
```
DATABASE_URL = postgresql://postgres.PROJETO:SENHA@aws-0-us-west-2.pooler.supabase.com:6543/postgres
```
- Usa Session Pooler (porta 6543) — compatível com IPv4
- Conexão direta (porta 5432) usa IPv6 — NÃO funciona em redes IPv4-only

---

## Fluxo de uma requisição

### Requisição pública (ex: acessar um post)

```
1. Browser → DNS → IP SEU_IP:443
2. Nginx recebe a requisição HTTPS
3. Nginx valida SSL (Let's Encrypt)
4. Nginx adiciona headers de segurança
5. Nginx faz proxy para unix:/run/ageu/ageu.sock
6. Gunicorn (worker disponível) recebe a requisição
7. Flask roteia para views.py → função post(post_id)
8. SQLAlchemy consulta Supabase via pooler
9. Jinja2 renderiza o template post.html
10. Response volta pelo mesmo caminho
11. Nginx entrega ao browser com headers de segurança
```

### Publicação de post (admin)

```
1. Admin acessa /admin/create_post (verificado login_required)
2. Preenche título, conteúdo (QuillJS), seleciona tags
3. POST → admin.py → create_post()
4. bleach.clean() sanitiza o título
5. clean_content() sanitiza o HTML do Quill (bleach)
6. Post salvo no banco (db.session.flush() para obter ID)
7. replace_inline_images_with_supabase() envia imagens base64 para Supabase Storage
8. URLs das imagens substituídas no conteúdo
9. Tags associadas via post_tags
10. db.session.commit()
11. Redirect para /admin/
```

### Comentário de visitante

```
1. Visitante preenche nome, site (opcional), comentário
2. POST /post/<id>
3. CSRF token validado pelo Flask-WTF
4. Comment salvo com is_author=False, seen=False
5. Redirect (PRG pattern — evita reenvio no F5)
6. Comentário aparece imediatamente (sem moderação)
```

### Comentário/resposta do admin

```
1. Admin logado vê botão "Responder" em cada comentário
2. Formulário inline aparece (JS showReplyForm())
3. POST com parent_id preenchido
4. Comment salvo com is_author=True
5. Badge "Autor" aparece no comentário
```

---

## Camadas de segurança

### 1. Nível de rede (UFW)
```
Permite: 22 (SSH), 80 (HTTP), 443 (HTTPS)
Bloqueia: todo o resto por padrão
Ranges específicos bloqueados: 15+ ranges maliciosos conhecidos
```

### 2. Proteção SSH (Fail2ban)
- Bane após 3 tentativas erradas
- Banimento por 7 dias (604800 segundos)
- Janela de análise: 1 hora (3600 segundos)
- Ação ao banir: UFW block + notificação Telegram + report AbuseIPDB

### 3. Nginx (proxy reverso)
Headers de segurança aplicados em todas as respostas:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: (ver abaixo)
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

CSP completo (fonte da verdade: `docs/setup-vps.sh`):
```
default-src 'self';
script-src 'self' 'unsafe-inline' https://darkvisitors.com https://gc.zgo.at https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
font-src 'self' data:;
img-src 'self' data: https:;
connect-src 'self' https://ageu.goatcounter.com https://darkvisitors.com;
```
> FontAwesome foi removido (SVGs inline). O Quill (admin) é carregado de `cdn.jsdelivr.net`.

### 4. Aplicação Flask
- **CSRF:** Flask-WTF em todos os formulários
- **XSS:** Bleach sanitiza posts/notas; comentários são escapados pelo Jinja; campo `website` validado no servidor (http/https)
- **Rate limiting:** Flask-Limiter, 10 req/min no POST de login e 5 req/min no POST de comentário — com `ProxyFix`, o limite é por IP real do cliente (X-Forwarded-For do Nginx)
- **Autenticação:** sessão Flask com login_required decorator
- **Senha admin:** hash pbkdf2 via werkzeug
- **Auditoria:** bandit 0 issues no código

### 5. Banco de dados (Supabase)
- RLS habilitado em todas as tabelas
- Credenciais apenas no .env (chmod 600, fora do git)
- Nunca exposto diretamente — sempre via aplicação

---

## Deploy automático

### Fluxo completo

```
Desenvolvedor (Windows)
  ↓ git push origin master
GitHub (repositório privado)
  ↓ dispara workflow
GitHub Actions (runner ubuntu-latest)
  ↓ SSH com deploy_key2
VPS
  ↓ executa script:
    cd /var/www/app/app
    git pull origin master
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    systemctl restart ageu
  ↓ Gunicorn reinicia com código novo
Blog atualizado (~20 segundos total)
```

### Secrets do GitHub Actions
| Secret      | Descrição                                |
| ----------- | ---------------------------------------- |
| VPS_HOST    | IP da VPS                                |
| VPS_USER    | root                                     |
| VPS_SSH_KEY | Chave privada SSH dedicada (deploy_key2) |

---

## Monitoramento

### UptimeRobot
- Monitora `https://ageu.blog/health` a cada 5 minutos
- Verifica keyword `"ok"` no JSON de resposta
- Alerta por email se o site cair ou banco não responder

### GoatCounter
- Analytics de privacidade (sem cookies)
- Dashboard em ageu.goatcounter.com
- Script: `//gc.zgo.at/count.js`

### Fail2ban + AbuseIPDB + Telegram
- Cada IP banido → notificação Telegram imediata
- Cada IP banido → report automático para AbuseIPDB com categorias 18 (Brute Force) + 22 (SSH)
- Log local: `/var/log/abuseipdb.log`

### Google Search Console
- Site verificado via metatag no index.html
- Sitemap submetido: `https://ageu.blog/sitemap.xml`

---

## Serviços externos utilizados

| Serviço               | URL                 | Finalidade                | Obrigatório |
| --------------------- | ------------------- | ------------------------- | ----------- |
| Supabase              | supabase.com        | Banco + Storage           | Sim         |
| GitHub                | github.com          | Repositório + CI/CD       | Sim         |
| Let's Encrypt         | letsencrypt.org     | SSL gratuito              | Sim         |
| GoatCounter           | goatcounter.com     | Analytics                 | Não         |
| SVG inline (ícones)   | —                   | Ícones (sem CDN)          | Sim         |
| DarkVisitors          | darkvisitors.com    | Bloqueio de bots          | Não         |
| AbuseIPDB             | abuseipdb.com       | Reporte de IPs maliciosos | Não         |
| UptimeRobot           | uptimerobot.com     | Monitoramento             | Não         |
| Google Search Console | search.google.com   | SEO/indexação             | Não         |

---

## Comandos essenciais de operação

### Status geral
```bash
systemctl status ageu nginx fail2ban
curl -s https://ageu.blog/health
git log --oneline -5
```

### Logs
```bash
journalctl -u ageu -n 50 -f          # logs Flask/Gunicorn em tempo real
journalctl -u nginx -n 20            # logs Nginx
tail -f /var/log/fail2ban.log         # logs Fail2ban
tail -f /var/log/abuseipdb.log        # logs AbuseIPDB
```

### Manutenção
```bash
systemctl restart ageu                # reiniciar aplicação
nginx -t && systemctl reload nginx    # recarregar Nginx
systemctl restart fail2ban            # reiniciar Fail2ban
fail2ban-client status sshd           # ver IPs banidos
fail2ban-client unban IP              # desbanir IP
```

### Git / Deploy
```bash
git log --oneline -5                  # commits na VPS
git fetch origin && git status        # verificar se está atualizado
git stash && git pull origin master   # resolver conflito (hotfix na VPS)
```

### Backup manual
```bash
bash /root/backup-config.sh           # backup das configs do servidor
```

---

## Problemas conhecidos e soluções

### "Your local changes would be overwritten by merge"
Acontece quando um arquivo foi editado diretamente na VPS e depois houve um push do Windows.
```bash
git stash
git pull origin master
systemctl restart ageu
```
**Prevenção:** NUNCA editar arquivos diretamente na VPS. Sempre editar no Windows e fazer push.

### Blog não atualiza após deploy
```bash
git log --oneline -3                  # verificar se o commit chegou
git fetch origin
git status                            # se desatualizado:
git pull origin master
systemctl restart ageu
```

### Erro 500
```bash
journalctl -u ageu -n 100            # ver traceback completo
curl http://localhost:5000/health     # testar sem Nginx
```

### Fail2ban baniu seu próprio IP
```bash
curl ifconfig.me                      # ver seu IP atual
fail2ban-client unban SEU_IP
```

### Banco não conecta
```bash
curl -s https://ageu.blog/health      # verificar status
# Se database: error:
# 1. Verificar painel Supabase (supabase.com/dashboard)
# 2. Verificar DATABASE_URL no .env
cat /var/www/app/app/.env | grep DATABASE_URL
```

---

## Permissões importantes

```bash
chmod 600 /var/www/app/app/.env
chmod 600 ~/.ssh/deploy_key2
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod +x /etc/fail2ban/notify-telegram.sh
chmod +x /etc/fail2ban/abuseipdb-report.sh
chmod +x /root/backup-config.sh
```

---

## O que NÃO está no GitHub

| O que            | Onde fica                              | Por quê           |
| ---------------- | -------------------------------------- | ----------------- |
| `.env`           | `/var/www/app/app/.env`                | Senhas e tokens   |
| Token Telegram   | `/etc/fail2ban/notify-telegram.sh`     | Credencial do bot |
| Chave SSH        | `~/.ssh/deploy_key2`                   | Acesso à VPS      |
| Config Nginx     | `/etc/nginx/sites-available/ageu.blog` | Infraestrutura    |
| Config Fail2ban  | `/etc/fail2ban/jail.local`             | Infraestrutura    |
| Script AbuseIPDB | `/etc/fail2ban/abuseipdb-report.sh`    | Contém API key    |

---

## Pendências conhecidas

- [ ] Expiração de sessão do admin (`PERMANENT_SESSION_LIFETIME = 2h`)
- [x] FontAwesome removido — ícones SVG inline (sem CDN, sem SRI)
- [ ] Formatação Quill quebrada nos posts (classes `ql-*` sem CSS no post.html)
- [ ] SSH por chave sem senha (requer VPS com console VNC)
- [ ] Backup automático via cron
- [ ] Notificação de novos comentários (Telegram ou email)
- [ ] Atualizar repositório open source (github.com/Ageursilva/ageublog)
