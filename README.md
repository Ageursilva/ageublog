
# Ageu Blog Template
Este é o modelo que desenvolvi para o meu ["Jardim Digital"](https://weeklymusings.net/weekly-musings-092) uso ele em meu [blog](https://ageu.tech/) pessoal. A ideia aqui é que você possa utilizar e aprimorar para o seu uso. Tentei criar algo clean, simples e visualmente agradável para que qualquer pessoa possa usar. 


Fique à vontade para usá-lo, editar e melhorar. Desculpe pela bagunça no código, um dia irei refatorar 😄.


## Visão Geral

O blog oferece um layout clean e responsivo, com uma estrutura simplificada para a criação e exibição de posts. Ele é ideal para quem quer um espaço de escrita minimalista, sem distrações.

## Tecnologias Usadas

- **Front-end**: HTML5, CSS3, JavaScript (Quill para o editor).
- **Back-end**: Flask, Jinja2, SQLite, Python.
- **Integrações**: Utteranc para comentários.

## Funcionalidades

- Design simples e responsivo.
- Editor de posts com Quill.
- Paginação de posts.
- Área administrativa com autenticação.
- Sistema de comentários com Utteranc.

## Como Instalar e Configurar

### 1. Clonar o Repositório

```bash
git clone https://github.com/Ageursilva/IdilioEfemero.git
cd IdilioEfemero 
```
### 2. Criar Ambiente Virtual e Instalar Dependências

```bash
python -m venv venv
source venv/bin/activate  # No Windows use `venv\Scripts\activate`
pip install -r requirements.txt`` 
```
### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` ou modifique o arquivo `config.py` para incluir a `SECRET_KEY` e outras configurações.

**Gerando a SECRET_KEY:**

```python
import secrets
print(secrets.token_hex(16))  # Gera uma chave secreta` 
```
Adicione a chave no arquivo `app.py`:

`app.config['SECRET_KEY'] =  'coloque_sua_chave_aqui'` 

### 4. Inicializar o Banco de Dados

```bash
flask db init
flask db migrate
flask db upgrade 
```
### 5. Criar um Usuário Administrador

```bash
flask shell
```
Dentro do shell do Flask, execute o seguinte código:

```python
from app import app, db, User
with app.app_context():
    admin = User(username='admin')
    admin.set_password('adminpassword')
    db.session.add(admin)
    db.session.commit()` 
```
### 6. Configurando o Utteranc para Comentários

1.  Acesse o repositório do [Utteranc no GitHub](https://github.com/apps/utterances) e instale ele em seu repositório.
2.  No arquivo `post.html`, edite o código do Utteranc:

```html
<script src="https://utteranc.es/client.js"
	 repo="seu-usuario/seu-repositorio"
	 issue-term="pathname"
	 theme="github-light"
	 crossorigin="anonymous"
	 async>
</script> 
```
Substitua `"seu-usuario/seu-repositorio"` pelo caminho do seu repositório GitHub.
## RSS e Sitemap

Atualmente, o blog ainda não gera automaticamente o **RSS feed** e o **sitemap**. Isso significa que, para quem deseja utilizar essas funcionalidades, será necessário criar e atualizar manualmente ambos os arquivos, fiquei olhando algumas formas de fazer isso automaticamente, mas a realidade é que apenas fui atrás disso depois de publicar o site, então, em algum momento devo corrigir essa questão.

## Contribuições

Contribuições são bem-vindas! Abra um issue ou envie um pull request.

## Licença

Este projeto está licenciado sob a [Licença Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pt-br).

> "Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity." — **Aaron Swartz**
> 
## Colaboradores
<table align="center">
  <tr>
    <td align="center">
      <a href="https://www.linkedin.com/in/ageursilva/">
        <img src="https://github.com/Ageursilva.png" width="100px;"><br />
        <sub><b>Ageu Silva</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://www.linkedin.com/in/vitor-alvim-604080319">
        <img src="https://media.licdn.com/dms/image/v2/D4D03AQEL93hazzngUQ/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1726180928093?e=1731542400&v=beta&t=iVcPXTvjunD5bleqXIa68GNY5ovqJowzeYGCqjdKgb8" width="100px;"><br />
        <sub><b>Vitor Alvim </b></sub>
      </a>
    </td>
  </tr>
</table>





<p align="center">
<a href="https://github.com/Ageursilva/IdilioEfemero">
<img src="https://img.shields.io/github/forks/Ageursilva/IdilioEfemero?style=social&label=Fork" alt="Forks">
</a>
<a href="https://github.com/Ageursilva/IdilioEfemero">
<img src="https://img.shields.io/github/stars/Ageursilva/IdilioEfemero?style=social&label=Star" alt="Stars">
</a>
<img src="https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg" alt="License: CC BY-NC-SA 4.0">
<img src="https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow.svg" alt="Status: Em Desenvolvimento">
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
<img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">

</p> 
