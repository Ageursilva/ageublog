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
 -  Design simples, responsivo e com tema escuro.
-  Editor de posts com [QuillJS](https://quilljs.com/).
-   **Segurança Reforçada:**
-  Proteção contra CSRF em todos os formulários.
-  Sanitização de HTML (XSS) no conteúdo dos posts.
-   **Geração Automática de Feeds:**
-  RSS feed (`/feed`) gerado dinamicamente.
-  Sitemap (`/sitemap.xml`) gerado dinamicamente para melhor SEO.
-   **Arquitetura Modular:**
-  Separação clara de responsabilidades com Blueprints.
-  Fácil manutenção e escalabilidade.
-   Paginação de posts na home e no painel de admin.
-   Área administrativa protegida com autenticação.
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
│ ├── __init__.py # Factory do Flask, inicializa blueprints
│ ├── config.py # Configurações da aplicação
│ ├── models.py # Modelos SQLAlchemy (User, Post)
│ ├── views.py # Blueprint de rotas públicas
│ ├── admin.py # Blueprint de admin e autenticação
│ ├── utils.py # Funções auxiliares (sanitização, autenticação)
│ │
│ ├── templates/ # Templates Jinja2
│ │ ├── base.html
│ │ ├── index.html
│ │ ├── post.html
│ │ ├── about.html
│ │ ├── login.html
│ │ ├── admin.html
│ │ ├── 404.html
│ │ ├── 500.html
│ │ ├── feed.xml
│ │ └── sitemap.xml
│ │
│ └── static/ # Arquivos estáticos
│ ├── style.css # Estilos CSS
│ ├── script.js # Scripts JavaScript
│ ├── logo.png
│ └── favicon.ico
│
├── run.py # Ponto de entrada da aplicação
├── requirements.txt # Dependências do projeto
├── blog.db # Banco de dados SQLite (gerado)
├── README.md # Versão em inglês
└── README.pt.md # Este arquivo
```

  

##  Como Instalar e Configurar
###  1. Clonar o Repositório
```bash
git  clone  https://github.com/Ageursilva/ageublog.git
cd  ageublog
```
###  2. Criar Ambiente Virtual e Instalar Dependências
É crucial usar um ambiente virtual para isolar as dependências do projeto.
```bash
# Criar o ambiente
python3  -m  venv  venv

# Ativar o ambiente

# No Linux/macOS:
source  venv/bin/activate

# No Windows:
venv\Scripts\activate

# Instalar as dependências

pip  install  -r  requirements.txt

```
###  3. Configurar a Chave Secreta
A aplicação precisa de uma `SECRET_KEY` para funcionar. A forma mais segura é usando variáveis de ambiente.

**Abra o arquivo `app/config.py`** e encontre a linha:
```python
SECRET_KEY  = os.environ.get('SECRET_KEY', 'change-me')
```
Para definir a variável de ambiente:
**Linux/macOS:**

```bash
export SECRET_KEY=$(python  -c  "import secrets; print(secrets.token_hex(16))")
```
**Windows (PowerShell):**

```powershell
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(16))")
```
Ou edite diretamente em `app/config.py` para testes locais.

###  4. Inicializar o Banco de Dados
Com o ambiente virtual ativado, rode o seguinte comando no terminal.

```bash
# Cria o arquivo blog.db e as tabelas
python  run.py
```
Na primeira execução, o Flask criará o banco de dados automaticamente.
###  5. Criar um Usuário Administrador

Use o shell do Flask para criar seu primeiro usuário.
```bash
python  -c  "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
admin = User(username='seu_usuario')
admin.set_password('sua_senha_forte')
db.session.add(admin)
db.session.commit()
print('Usuário criado com sucesso!')
"
```
###  6. Rodar a Aplicação
**Modo desenvolvimento:**

```bash
python  run.py
```
**Modo produção (com Gunicorn):**
```bash
gunicorn  --workers  4  --bind  0.0.0.0:8000  run:app
```
Acesse `http://127.0.0.1:5000` (ou `http://127.0.0.1:8000` se usar Gunicorn) no seu navegador.
Para acessar a área de admin, vá para `/admin/login`.
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
Este template foi testado com várias soluções de comentários. Escolha a que melhor se adapta a você:
-  **Giscus:** Usa as "Discussions" do GitHub. Leve, moderno e com reações/respostas.
-  **Cusdis:** Excelente opção focada em privacidade que permite comentários anônimos.
-  **Utterances:** Usa as "Issues" do GitHub. Uma alternativa sólida e simples.
Para implementar, basta substituir o script de comentários no final do arquivo `templates/post.html`.


##  Contribuições
Contribuições são muito bem-vindas! Sinta-se à vontade para:
-  Abrir uma issue para relatar um bug
-  Sugerir uma melhoria
-  Enviar um pull request
##  Licença
 Este projeto está licenciado sob a [Licença Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pt-br).
<br>