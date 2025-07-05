
<p align="right">
  <a href="./README.md">Português</a> | <a href="./README.en.md">English</a>
</p>

# Ageu Blog Template
Este é o modelo que desenvolvi para o meu ["Jardim Digital"](https://weeklymusings.net/weekly-musings-092) uso ele em meu [blog](https://ageu.tech/) pessoal. A ideia aqui é que você possa utilizar e aprimorar para o seu uso. Tentei criar algo clean, simples e visualmente agradável para que qualquer pessoa possa usar.

Fique à vontade para usá-lo, bifurcar (fork) e aprimorar. O código passou por uma grande revisão de segurança e funcionalidades recentemente, então posso dizer que é uma V2(?).

> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**

## Visão Geral
O blog oferece um layout clean e responsivo, otimizado para uma experiência agradável. A estrutura foi pensada para ser simples de instalar e manter, ideal para quem busca um espaço de escrita pessoal e seguro.

## Funcionalidades
- ✅ Design simples, responsivo e com tema escuro.
- ✍️ Editor de posts com [QuillJS](https://quilljs.com/).
- 🔒 **Segurança Reforçada:**
    - Proteção contra CSRF em todos os formulários.
    - Sanitização de HTML (XSS) no conteúdo dos posts.
- ⚙️ **Geração Automática de Feeds:**
    - RSS feed (`/feed`) gerado dinamicamente.
    - Sitemap (`/sitemap.xml`) gerado dinamicamente para melhor SEO.
	-  Paginação de posts na home e no painel de admin.
	-  Área administrativa protegida com autenticação.
## Tecnologias Usadas
- **Backend**: Python, Flask, Jinja2
- **Banco de Dados**: SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Segurança**: Flask-WTF (CSRF), Bleach (XSS)
- **Editor**: QuillJS

## Como Instalar e Configurar

### 1. Clonar o Repositório
```bash
git clone https://github.com/Ageursilva/ageublog.git
cd ageublog
```

### 2. Criar Ambiente Virtual e Instalar Dependências
É crucial usar um ambiente virtual para isolar as dependências do projeto.
```bash
# Criar o ambiente
python3 -m venv venv

# Ativar o ambiente
# No Linux/macOS:
source venv/bin/activate
# No Windows:
# venv\Scripts\activate

# Instalar as dependências
pip install -r requirements.txt
```

### 3. Configurar a Chave Secreta
A aplicação precisa de uma `SECRET_KEY` para funcionar. A forma mais segura é usando variáveis de ambiente, mas para um início rápido, você pode editá-la diretamente.

**Abra o arquivo `app.py`** e encontre a linha:
`app.config['SECRET_KEY'] = 'coloque_sua_chave_aqui'`

Substitua `'coloque_sua_chave_aqui'` por uma chave forte. Para gerar uma, use o terminal Python:
```python
import secrets; print(secrets.token_hex(16))
```

### 4. Inicializar o Banco de Dados
Com o ambiente virtual ativado, rode o seguinte comando no terminal:
```bash
# Este comando usa o contexto da aplicação para criar o arquivo .db e as tabelas.
python -c "from app import db; from app.models import User, Post; db.create_all()"
```

### 5. Criar um Usuário Administrador
Use o shell do Flask para criar seu primeiro usuário.
```bash
flask shell
```
Dentro do shell, execute o seguinte código:
```python
# Importa as ferramentas necessárias
from app import db
from app.models import User # Ou importe de app se não modularizou

# Cria o usuário
admin = User(username='seu_usuario')
admin.set_password('sua_senha_forte')

# Salva no banco de dados
db.session.add(admin)
db.session.commit()

# Saia do shell com exit()
exit()
```

### 6. Rodar a Aplicação
```bash
flask run
```
Acesse `http://127.0.0.1:5000` no seu navegador. Para acessar a área de admin, vá para `/login`.

## Sistema de Comentários
Este template foi testado com várias soluções de comentários. Escolha a que melhor se adapta a você:

- **Giscus:** Usa as "Discussions" do GitHub. Leve, moderno e com reações/respostas.
- **Cusdis:** Excelente opção focada em privacidade que permite comentários anônimos.
- **Utterances:** Usa as "Issues" do GitHub. Uma alternativa sólida e simples.

Para implementar, basta substituir o script de comentários no final do arquivo `templates/post.html`.

## Contribuições
Contribuições são muito bem-vindas! Sinta-se à vontade para abrir uma issue para relatar um bug ou sugerir uma melhoria, ou enviar um pull request.

## Licença
Este projeto está licenciado sob a [Licença Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pt-br).

<br>

## Colaboradores
<table align="center">
  <tr>
    <td align="center">
      <a href="https://www.linkedin.com/in/ageursilva/">
        <img src="https://github.com/Ageursilva.png" width="100px;" alt="Ageu Silva"/><br />
        <sub><b>Ageu Silva</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://www.linkedin.com/in/vitor-alvim-604080319">
        <img src="https://media.licdn.com/dms/image/v2/D4D03AQF0SMMjk3UIeA/profile-displayphoto-shrink_800_800/B4DZY7t8YkG4Ac-/0/1744758622504?e=1756944000&v=beta&t=yYcfOzQWCWoHKBYZH9Qe6BBIQiToa_Y_ljLEHIPdnbc" width="100px;" alt="Vitor Alvim"/><br />
        <sub><b>Vitor Alvim</b></sub>
      </a>
    </td>
  </tr>
</table>

<p align="center">
<a href="https://github.com/Ageursilva/ageublog">
<img src="https://img.shields.io/github/forks/Ageursilva/ageublog?style=social&label=Fork" alt="Forks">
</a>
<a href="https://github.com/Ageursilva/ageublog">
<img src="https://img.shields.io/github/stars/Ageursilva/ageublog?style=social&label=Star" alt="Stars">
</a>
<img src="https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg" alt="License: CC BY-NC-SA 4.0">
<img src="https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow.svg" alt="Status: Em Desenvolvimento">
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
<img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">

</p>