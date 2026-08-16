# Guia de Contribuição

Obrigado pelo seu interesse em contribuir para este projeto! Este guia ajudará
você a configurar o ambiente de desenvolvimento e garantir que as suas
contribuições estejam de acordo com os padrões do projeto.

## Requisitos

- Python 3.8+
- Flask
- SQLite (padrão, para desenvolvimento) ou PostgreSQL/Supabase
- Outras dependências listadas no `requirements.txt`

## Configuração do Ambiente

1. **Clone o repositório**:
    ```bash
    git clone https://github.com/Ageursilva/ageublog.git
    cd ageublog
    ```

2. **Crie e ative o ambiente virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate   # Linux/macOS
    venv\Scripts\activate      # Windows
    ```

3. **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt   # para a suíte de testes
    ```

4. **Configure o ambiente**:
   Copie o `.env.example` para `.env` e defina ao menos a `SECRET_KEY`
   (a aplicação se recusa a iniciar sem ela):
    ```bash
    cp .env.example .env
    ```

5. **Crie o banco de dados e o usuário admin** (apenas na primeira vez):
    ```bash
    python -c "
    from app import create_app, db
    from app.models import User
    app = create_app()
    with app.app_context():
        db.create_all()
        admin = User(username='admin')
        admin.set_password('sua_senha_forte')
        db.session.add(admin)
        db.session.commit()
        print('Admin criado: admin')
    "
    ```

6. **Rode a aplicação**:
    ```bash
    python run.py
    ```
    O projeto estará disponível em `http://localhost:5000`.

## Estrutura do Projeto

- `app/`: Pacote da aplicação Flask (factory, models, views, admin, utils).
- `app/templates/`: Templates Jinja2.
- `app/static/`: Arquivos estáticos (CSS, JS, ícones).
- `run.py`: Entry point da aplicação.
- `tests/`: Testes automatizados (pytest).
- `requirements.txt` / `requirements-dev.txt`: Dependências.

## Rodando os Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Contribuindo com Código

1. **Fork o repositório** e crie uma nova branch:
    ```bash
    git checkout -b nome-da-feature
    ```

2. **Escreva código limpo e documentado**:
   - Siga o padrão PEP8 para Python.
   - Comente trechos de código que possam não ser claros para outros desenvolvedores.
   - Mantenha o padrão de formatação do HTML e CSS do projeto para consistência.

3. **Adicione testes** (se aplicável):
   - Crie testes unitários para novas funcionalidades ou correções de bugs.
   - Certifique-se de que todos os testes estão passando antes de enviar.

4. **Atualize a documentação**:
   - Se sua alteração adiciona ou modifica uma funcionalidade, atualize os arquivos de documentação apropriados.

5. **Commit e push**:
    ```bash
    git commit -m "Descrição clara do commit"
    git push origin nome-da-feature
    ```

6. **Abra um Pull Request**:
   - Explique o que foi adicionado ou alterado e por que.
   - Aguarde pelo feedback e faça ajustes, se necessário.

## Padrões de Commit

- `feat`: Adição de uma nova funcionalidade.
- `fix`: Correção de um bug.
- `docs`: Alterações na documentação.
- `style`: Alterações de formatação (espaços, ponto-e-vírgula, etc).
- `refactor`: Refatoração de código sem alteração de funcionalidade.
- `test`: Adição ou modificação de testes.

Exemplo:
```bash
git commit -m "feat: adiciona funcionalidade de notas no painel de admin"
```