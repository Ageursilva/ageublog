
# Guia de Contribuição

Obrigado pelo seu interesse em contribuir para o nosso projeto! Este guia ajudará você a configurar o ambiente de desenvolvimento e garantir que as suas contribuições estejam de acordo com os padrões do projeto.

## Requisitos

- **Python 3.8+**
- **Flask**
- **Flask-Migrate** (para gerenciar as migrações do banco de dados)
- **Banco de Dados**: SQLite (para desenvolvimento) ou outro banco de sua escolha
- **Outras Dependências**: listadas no `requirements.txt`

## Configuração do Ambiente

1. **Clone o repositório**:
    ```bash
    git clone https://github.com/Ageursilva/ageublog.git
    cd seu-repositorio
    ```

2. **Crie e ative o ambiente virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Para Linux/Mac
    venv\Scripts\activate     # Para Windows
    ```

3. **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Configurar as variáveis de ambiente**:
   Crie um arquivo `.env` na raiz do projeto para armazenar as variáveis de ambiente necessárias, como `SECRET_KEY` e configurações do banco de dados. Exemplo:
   
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    SECRET_KEY=your_secret_key
    ```

5. **Configure o Banco de Dados**:
   Inicie o banco de dados e execute as migrações:
   
    ```bash
    flask db upgrade
    ```

6. **Inicie o servidor**:
    ```bash
    flask run
    ```

O projeto estará disponível em `http://localhost:5000`.

## Estrutura do Projeto

Aqui está uma visão geral da estrutura do projeto:

- `app.py`: Arquivo principal da aplicação Flask.
- `models.py`: Modelos de banco de dados.
- `templates/`: Diretório contendo os templates HTML.
- `static/`: Diretório para arquivos estáticos como CSS e JavaScript.
- `requirements.txt`: Arquivo contendo as dependências do projeto.

## Contribuindo com Código

1. **Fork o repositório** e crie uma nova branch para sua contribuição:
    ```bash
    git checkout -b nome-da-feature
    ```

2. **Escreva código limpo e documentado**:
   - Siga o padrão PEP8 para Python.
   - Comente trechos de código que possam não ser claros para outros desenvolvedores.
   - Siga o padrão de formatação do HTML e CSS do projeto para manter a consistência.

3. **Adicione testes** (se aplicável):
   - Crie testes unitários para novas funcionalidades ou correções de bugs.
   - Certifique-se de que todos os testes estão passando antes de enviar sua contribuição.

4. **Atualize a documentação**:
   - Se sua alteração adiciona uma nova funcionalidade ou altera uma funcionalidade existente, atualize os arquivos de documentação apropriados.

5. **Commit e push** suas alterações:
    ```bash
    git commit -m "Descrição clara do commit"
    git push origin nome-da-feature
    ```

6. **Abra um Pull Request**:
   - Explique o que foi adicionado ou alterado e por que.
   - Aguarde pelo feedback e faça ajustes, se necessário.

## Padrões de Commit

Para garantir a consistência nos commits, siga o padrão abaixo:

- `feat`: Adição de uma nova funcionalidade.
- `fix`: Correção de um bug.
- `docs`: Alterações na documentação.
- `style`: Alterações de formatação (espaços, ponto-e-vírgula, etc).
- `refactor`: Refatoração de código sem alteração de funcionalidade.
- `test`: Adição ou modificação de testes.

Exemplo:
```bash
git commit -m "feat: adiciona funcionalidade de notas no painel de admin"
