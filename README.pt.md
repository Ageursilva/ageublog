[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/V7V619VJBK)
<p align="right">
<a href="./README.md">Inglês</a> | <a href="./README.pt.md">Português</a>
</p>

  #  Ageu Blog Template
Este é o modelo que desenvolvi para o meu ["Jardim Digital"](https://weeklymusings.net/weekly-musings-092) usado em meu [blog](https://ageu.blog/) pessoal. A ideia aqui é que você possa utilizar e aprimorar para o seu uso. Tentei criar algo clean, simples e visualmente agradável para que qualquer pessoa possa usar.
Fique à vontade para usá-lo, bifurcar (fork) e aprimorar. O código passou por uma grande revisão de segurança e funcionalidades recentemente, além de ter sido **refatorado para uma arquitetura modular profissional**.
 
> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**  
##  Visão Geral

  O blog oferece um layout clean e responsivo, otimizado para uma experiência agradável. A estrutura foi pensada para ser simples de instalar e manter, ideal para quem busca um espaço de escrita pessoal e seguro. Agora com **arquitetura modular usando Blueprints do Flask**, facilitando manutenção e escalabilidade.

##  Funcionalidades

**Conteúdo**
- Posts com editor de texto rico ([QuillJS](https://quilljs.com/)).
- Tags para organizar os posts (`/tag/<nome>`).
- Notas — posts curtos em Markdown (`/notas`).
- Radar Cultural — um post fixado para recomendações culturais.
- Busca por texto completo (`/search?query=...`).
- Paginação na home, nas tags e no painel admin.

**Comentários**
- Sistema de comentários nativo (sem serviço de terceiros): respostas,
  selo de autor e fila de moderação no painel admin.

**Segurança**
- Proteção CSRF em todos os formulários (Flask-WTF).
- Sanitização de HTML (Bleach) no conteúdo de posts e comentários.
- Validação no servidor do campo `website` (bloqueia `javascript:`/`data:`).
- Rate limit no login e nos comentários (por IP real, atrás de proxy).
- Sessões seguras (HttpOnly, SameSite, Secure em produção) e logout só via POST.
- Roda como serviço sem privilégios em produção.

**Performance e SEO**
- RSS feed (`/feed`) gerado dinamicamente.
- Sitemap (`/sitemap.xml`) gerado dinamicamente.
- Dados estruturados JSON-LD (`BlogPosting`) nos posts.
- Ícones SVG inline — sem CDN de ícones.
- Estáticos servidos direto pelo Nginx com cache (produção).

**Arquitetura**
- Aplicação Flask modular com application factory e Blueprints.
- SQLite por padrão; PostgreSQL/Supabase opcional.
- Design minimalista, limpo e com tema escuro — sem frameworks CSS pesados.

##  Tecnologias Usadas
-  **Backend**: Python, Flask, Jinja2
-  **Banco de Dados**: SQLAlchemy, SQLite
-  **Frontend**: HTML5, CSS3, JavaScript
-  **Segurança**: Flask-WTF (CSRF), Bleach (XSS)
-  **Editor**: QuillJS
##  Estrutura do Projeto

```
ageublog/
│
├── app/
│   ├── __init__.py      # Flask factory, blueprints, config de segurança
│   ├── config.py        # Configuração (baseada em env)
│   ├── models.py        # Modelos SQLAlchemy (User, Post, Comment, Tag, Note)
│   ├── views.py         # Rotas públicas (Blueprint)
│   ├── admin.py         # Rotas admin + autenticação
│   ├── utils.py         # Helpers (saneamento, auth, upload de imagem)
│   │
│   ├── templates/       # Templates Jinja2 (posts, admin, feed, sitemap...)
│   └── static/          # style.css, script.js, favicon.ico
│
├── run.py               # Entry point da aplicação
├── requirements.txt     # Dependências
├── requirements-dev.txt # Dependências de dev/teste (pytest)
├── .env.example         # Template de variáveis de ambiente
├── docs/                # Docs de arquitetura e deploy
├── LICENSE
└── README.md / README.pt.md
```
##  Como Instalar e Configurar

###  1. Clonar o Repositório

```bash
git clone https://github.com/Ageursilva/ageublog.git
cd ageublog
```

###  2. Criar Ambiente Virtual e Instalar Dependências

```bash
python3 -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

pip install -r requirements.txt
# Opcional, para rodar os testes:
pip install -r requirements-dev.txt
```

###  3. Configurar o Ambiente (`.env`)

A aplicação precisa de uma `SECRET_KEY` e **se recusa a iniciar sem ela**.
Copie o arquivo de exemplo e defina seus valores:

```bash
cp .env.example .env
```

Depois edite o `.env` e defina `SECRET_KEY` com um valor forte e aleatório
(ex.: `python -c 'import secrets; print(secrets.token_hex(32))'`).

Por padrão o app usa **SQLite** (`sqlite:///app/blog.db`) — nenhum banco
externo é necessário para começar. Para usar PostgreSQL/Supabase, defina
`DATABASE_URL` no `.env` (veja `.env.example` para todas as opções).

###  4. Criar o Banco de Dados e o Usuário Administrador

Rode uma vez para criar as tabelas e sua conta de admin:

```bash
python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('sua_senha_forte')
        db.session.add(admin)
        db.session.commit()
        print('Admin criado: admin')
    else:
        print('Admin ja existe')
"
```

###  5. Rodar a Aplicação

**Modo desenvolvimento:**
```bash
python run.py
```
**Modo produção (Gunicorn):**
```bash
gunicorn --workers 2 --bind 0.0.0.0:8000 run:app
```
Acesse `http://127.0.0.1:5000` (ou `http://127.0.0.1:8000` se usar Gunicorn).
Área de admin: `/admin/login`.

##  Arquitetura Modular
O projeto utiliza **Blueprints do Flask** para organizar as rotas em módulos independentes:
 
###  `app/__init__.py` - Factory Pattern

```python

def  create_app():

# Cria e configura a aplicação Flask
# Registra todos os blueprints
# Inicializa extensões (db, csrf)
```


###  `app/models.py` - Modelos de Dados

-  `User`: Modelo de usuário com autenticação

-  `Post`: Modelo de posts do blog 

###  `app/views.py` - Rotas Públicas

-  `/`: Home com paginação
-  `/post/<id>`: Página de post
-  `/about`: Página sobre
-  `/search`: Busca de posts
-  `/feed`: RSS feed
-  `/sitemap.xml`: Sitemap para SEO

###  `app/admin.py` - Rotas Administrativas

-  `/admin/login`: Autenticação
-  `/admin/`: Painel de controle
-  `/admin/create_post`: Criar novo post
-  `/admin/edit_post/<id>`: Editar post
-  `/admin/delete_post/<id>`: Deletar post
###  `app/utils.py` - Funções Auxiliares

-  `login_required()`: Decorator para proteger rotas
-  `clean_content()`: Sanitização de HTML
-  `extract_image_and_excerpt()`: Extrai imagem e resumo de posts
##  Sistema de Comentários

Sistema de comentários nativo (sem serviço de terceiros):

- Visitantes comentam nos posts, com nome e site opcionais.
- Respostas aos comentários (um nível).
- Comentários do admin recebem o selo de autor.
- Fila de moderação no painel admin (`/admin/comments`): marcar como visto ou excluir.
- Validação no servidor: o campo `website` só aceita `http`/`https`
  (bloqueia `javascript:`/`data:`), e o tamanho do conteúdo é limitado.

##  Contribuições
Contribuições são muito bem-vindas! Sinta-se à vontade para:
-  Abrir uma issue para relatar um bug
-  Sugerir uma melhoria
-  Enviar um pull request
##  Licença
 Este projeto está licenciado sob a [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html). Veja o arquivo `LICENSE`.
<br>