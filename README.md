# Ageu

Este é o modelo que desenvolvi para o  meu ["Jardim Digital"](https://weeklymusings.net/weekly-musings-092), a ideia aqui é que você possa utilizar e aprimorar para seu uso, tentei criar algo clean, simples e agradável visualmente para que todos que quiserem possam utilizar. 
Fique a vontade para usa-lo, editar e melhorar e desculpe pela bagunça no código, um dia irei refatorar .

## Visão Geral

O blog oferece um layout visualmente agradável e fácil de usar, com uma abordagem simples para a criação e exibição de posts.

## Tecnologias Usadas

- **HTML5** e **CSS3** para a estrutura e estilo do site.
- **JavaScript** e **Quill** para a edição de posts.
- **Flask** para o back-end e gerenciamento de posts.
- **SQLite** para o banco de dados.
- **Python** para lógica de back-end.
- **Jinja2** para renderização de templates.
- **Utteranc** para comentários nos posts.

## Funcionalidades

- Design clean e responsivo.
- Editor de postagens utilizando o Quill.
- Paginação para posts.
- Área administrativa com autenticação para gerenciar postagens.
- Comentários nos posts utilizando Utteranc.


## Como Configurar

### Gerando a Secret Key

Para gerar a `SECRET_KEY` para o Flask, execute o seguinte código em um ambiente Python:
```python
    python import secrets
    print(secrets.token_hex(16)) 
```
Copie a chave gerada e adicione-a ao seu arquivo de configuração (como `config.py` ou diretamente no código).

 ## Criando um Usuário para o Banco de Dados

Para criar um usuário administrador no banco de dados, siga os passos abaixo:

 1. **Iniciar o Flask:** Execute o comando `flask run` no terminal.   
 2. **Acessar o shell do Flask:** Pressione Ctrl+C para interromper o servidor e, em seguida, execute `flask shell`.  
 3. **Colar o código:** Cole o código Python no shell e pressione Enter para executá-lo.

```python
from app import app, db, User

with app.app_context():
    admin = User(username='User')
    admin.set_password('Password')
    db.session.add(admin)
    db.session.commit()
```
Substitua `'User'` pelo nome de usuário desejado e `'Password'` pela senha que deseja atribuir.

## Configurando o Utteranc
O Utteranc é utilizado para permitir que os visitantes comentem nos posts do blog utilizando suas contas GitHub. Ele já está configurado no arquivo `post.html`. Para personalizar ou ajustar a configuração, siga estes passos:

1.  Acesse o repositório do [Utteranc no GitHub](https://github.com/apps/utterances) e instale ele em seu repositório.
2.  No arquivo `post.html`, edite o código necessário para carregar o Utteranc:

``` html 
 <script src="https://utteranc.es/client.js"
	 repo="seu-usuario/seu-repositorio"
	 issue-term="pathname"
	 theme="github-light"
	 crossorigin="anonymous"
	 async>
</script>
```
3. Substitua `"seu-usuario/seu-repositorio"` pelo caminho do seu repositório GitHub onde os comentários serão armazenados.
## Próximos Passos

Estamos trabalhando na melhoria da documentação e na adição de novas funcionalidades. Em breve, você encontrará uma documentação mais detalhada sobre como configurar e usar o blog, bem como informações sobre possíveis extensões e personalizações.

## Contribuição

Como este é um projeto pessoal, as contribuições são bem-vindas!  Você pode fazer um fork e alterar da forma que desejar.

## Licença

Este projeto está licenciado sob a [Licença Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pt-br).

> *"Be curious. Read widely. Try new things. I think a lot of what people call intelligence boils down to curiosity.” 
> 	 **Aaron Swartz***
