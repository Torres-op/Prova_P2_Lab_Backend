# API de Produtos — FastAPI + SQLAlchemy + PostgreSQL

`Este projeto foi feito para fixar e treinar os aprendizados ensinados em sala.`

API REST para gerenciamento de um catálogo de produtos de um pequeno e-commerce,
com uma suíte de testes automatizados (Pytest + TestClient) que roda contra um
banco **PostgreSQL real** provisionado via Docker.

## Stack

- **FastAPI** — framework web
- **SQLAlchemy ORM** — mapeamento da tabela `produtos`
- **Pydantic** — validação de entrada e schema de saída
- **PostgreSQL** (Docker) — banco de desenvolvimento e banco de testes separados
- **Pytest** — suíte de testes automatizados

## Estrutura do projeto

```
p1-backend-test/
├── main.py              # API: modelo ORM, schemas, endpoints, get_db
├── conftest.py          # Fixtures: client (isolamento) e produto_existente
├── requirements.txt     # Dependências
├── docker-compose.yml   # Dois bancos: db (5432) e db_test (5433)
├── Dockerfile           # Imagem da API
├── pytest.ini           # Configuração do pytest
├── README.md
└── tests/
    ├── __init__.py
    └── test_produtos.py # 12 funções de teste
```

## Modelo de dados — Produto

| Campo   | Tipo    | Regra                                |
| ------- | ------- | ------------------------------------ |
| id      | Integer | Chave primária, gerada pelo banco    |
| nome    | String  | Obrigatório, não pode ser vazio      |
| preco   | Float   | Obrigatório, deve ser maior que zero |
| estoque | Integer | Padrão: `0`                          |
| ativo   | Boolean | Padrão: `True`                       |

## Endpoints

| Método | Rota             | Status    | Comportamento                      |
| ------ | ---------------- | --------- | ---------------------------------- |
| GET    | `/produtos`      | 200       | Lista todos os produtos            |
| POST   | `/produtos`      | 201       | Cria um produto e retorna com `id` |
| GET    | `/produtos/{id}` | 200 / 404 | Retorna o produto ou 404           |
| DELETE | `/produtos/{id}` | 204 / 404 | Remove o produto ou 404            |

---

## 1. Subir o banco de teste com Docker

Antes de rodar os testes, suba **apenas** o banco de testes (porta `5433`) e
confirme que o container está _healthy_:

```bash
docker-compose up -d db_test

# Verifica o status (deve aparecer "healthy")
docker-compose ps
```

Para também subir o banco de desenvolvimento (porta `5432`):

```bash
docker-compose up -d db
```

> O banco de testes **não** usa volume nomeado — os dados são descartáveis.
> Apenas o banco de desenvolvimento (`db`) persiste dados no volume `postgres_data`.

## 2. Instalar dependências

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Comando exato para executar os testes

```bash
python -m pytest --cov=main -v
```

> Use `python -m pytest` (e não apenas `pytest`). Se o diretório `Scripts` do
> Python não estiver no PATH, o comando `pytest` puro falha com
> `command not found` — chamar via `python -m` evita esse problema.
> Dentro de um virtualenv ativado (`source .venv/Scripts/activate`), o comando
> `pytest --cov=main -v` também funciona normalmente.

Comando de verificação final (sobe o banco e roda os testes com cobertura):

```bash
docker-compose up -d db_test && python -m pytest --cov=main -v
```

A suíte usa a variável de ambiente `TEST_DATABASE_URL`
(padrão: `postgresql://postgres:postgres@localhost:5433/produtos_test`).

## 4. Saída esperada do pytest

```text
$ pytest --cov=main -v
============================= test session starts =============================
platform win32 -- Python 3.12.x, pytest-8.2.2, pluggy-1.5.0
rootdir: d:\Codes\Testes\p1-backend-test
configfile: pytest.ini
plugins: cov-5.0.0, anyio-4.x
collected 18 items

tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED          [  5%]
tests/test_produtos.py::test_criar_produto_persistencia PASSED           [ 11%]
tests/test_produtos.py::test_criar_produto_aparece_na_listagem PASSED    [ 16%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 22%]
tests/test_produtos.py::test_buscar_produto_id_inexistente_retorna_404 PASSED [ 27%]
tests/test_produtos.py::test_deletar_produto_retorna_204 PASSED          [ 33%]
tests/test_produtos.py::test_deletar_produto_confirmacao_com_get PASSED  [ 38%]
tests/test_produtos.py::test_deletar_produto_inexistente_retorna_404 PASSED [ 44%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload0-nome vazio] PASSED [ 50%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload1-nome só espaços] PASSED [ 55%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload2-preço zero] PASSED [ 61%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload3-preço negativo] PASSED [ 66%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload4-nome ausente] PASSED [ 72%]
tests/test_produtos.py::test_criar_produto_payload_invalido_retorna_422[payload5-preço ausente] PASSED [ 77%]
tests/test_produtos.py::test_banco_isolado_entre_execucoes_parte_1 PASSED [ 83%]
tests/test_produtos.py::test_banco_isolado_entre_execucoes_parte_2 PASSED [ 88%]
tests/test_produtos.py::test_criar_produto_valores_padrao PASSED         [ 94%]
tests/test_produtos.py::test_listar_multiplos_produtos PASSED            [100%]

---------- coverage: platform win32, python 3.13.x ----------
Name      Stmts   Miss  Cover
-----------------------------
main.py      71      4    94%
-----------------------------
TOTAL        71      4    94%

============================= 18 passed in 7.35s ==============================
```

> Observação: os percentuais e tempos podem variar; o importante é que **todos
> os testes passem** e a cobertura de `main.py` fique acima de 85%.

## 5. Como funciona o isolamento entre testes

O isolamento é garantido pela fixture `client` (em `conftest.py`), com escopo
`function` (executada do zero a cada teste):

1. **`Base.metadata.create_all(bind=test_engine)`** — cria todas as tabelas no
   banco de testes (PostgreSQL na porta `5433`) **antes** do teste rodar.
2. **`app.dependency_overrides[get_db] = override_get_db`** — substitui a
   dependência `get_db` da aplicação por uma sessão apontando para o banco de
   testes, sem tocar no banco de desenvolvimento.
3. **`yield test_client`** — entrega o `TestClient` para a função de teste; é
   nesse ponto que o teste é executado.
4. **`Base.metadata.drop_all(bind=test_engine)`** — no teardown, derruba todas
   as tabelas, apagando qualquer dado criado durante o teste.
5. **`app.dependency_overrides.clear()`** — limpa os overrides.

Como `create_all` + `drop_all` acontecem a cada função, **cada teste recebe um
banco completamente vazio**. Por isso os testes passam independentemente da
ordem de execução, e nenhum teste depende de estado deixado por outro.

Os testes `test_banco_isolado_entre_execucoes_parte_1` e `parte_2` comprovam
isso: o primeiro cria um produto e confirma que ele existe; o segundo verifica
que o banco voltou a ficar vazio, provando que o teardown funcionou.

A fixture auxiliar `produto_existente` depende de `client` e cria um produto já
pronto para os testes que precisam de um registro pré-existente.
