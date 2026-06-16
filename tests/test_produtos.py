import pytest
from fastapi.testclient import TestClient


def test_listar_produtos_banco_vazio(client: TestClient):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []


def test_criar_produto_persistencia(client: TestClient):
    payload = {"nome": "Teclado Mecânico Y'shtola", "preco": 299.99, "estoque": 5}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None

    get_response = client.get(f"/produtos/{data['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["nome"] == "Teclado Mecânico Y'shtola"


def test_criar_produto_aparece_na_listagem(client: TestClient):
    payload = {"nome": "Mouse Gamer da Tiamat", "preco": 129.90}
    client.post("/produtos", json=payload)

    response = client.get("/produtos")
    assert response.status_code == 200
    nomes = [p["nome"] for p in response.json()]
    assert "Mouse Gamer da Tiamat" in nomes


def test_buscar_produto_por_id_sucesso(client: TestClient, produto_existente: dict):
    produto_id = produto_existente["id"]
    response = client.get(f"/produtos/{produto_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == produto_id
    assert data["nome"] == produto_existente["nome"]
    assert data["preco"] == produto_existente["preco"]


def test_buscar_produto_id_inexistente_retorna_404(client: TestClient):
    response = client.get("/produtos/9999")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"].lower()


def test_deletar_produto_retorna_204(client: TestClient, produto_existente: dict):
    produto_id = produto_existente["id"]
    response = client.delete(f"/produtos/{produto_id}")
    assert response.status_code == 204


def test_deletar_produto_confirmacao_com_get(client: TestClient, produto_existente: dict):
    produto_id = produto_existente["id"]

    delete_response = client.delete(f"/produtos/{produto_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/produtos/{produto_id}")
    assert get_response.status_code == 404


def test_deletar_produto_inexistente_retorna_404(client: TestClient):
    response = client.delete("/produtos/9999")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload,descricao",
    [
        ({"nome": "", "preco": 10.0}, "nome vazio"),
        ({"nome": "   ", "preco": 10.0}, "nome só espaços"),
        ({"nome": "Produto", "preco": 0}, "preço zerado"),
        ({"nome": "Produto", "preco": -5.0}, "preço negativo"),
        ({"preco": 10.0}, "nome ausente"),
        ({"nome": "Produto"}, "preço ausente"),
    ],
)
def test_criar_produto_payload_invalido_retorna_422(
    client: TestClient, payload: dict, descricao: str
):
    response = client.post("/produtos", json=payload)
    assert response.status_code == 422, f"Falhou para: {descricao}"


def test_banco_isolado_entre_execucoes_parte_1(client: TestClient):
    payload = {"nome": "Produto Isolado A", "preco": 1.0}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    assert len(client.get("/produtos").json()) == 1


def test_banco_isolado_entre_execucoes_parte_2(client: TestClient):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == [], (
        "O banco deveria estar vazio, mas contém dados do teste anterior. "
        "Verifique o teardown da fixture 'client'."
    )


def test_criar_produto_valores_padrao(client: TestClient):
    payload = {"nome": "Produto Mínimo", "preco": 9.99}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["estoque"] == 0
    assert data["ativo"] is True


def test_listar_multiplos_produtos(client: TestClient):
    produtos = [
        {"nome": "Cadeira Gamer Superfaturada", "preco": 899.00, "estoque": 3},
        {"nome": "Monitor 4K OLED Atraxa", "preco": 2499.00, "estoque": 1},
        {"nome": "Headset para The Ur-Dragon", "preco": 199.00, "estoque": 15},
    ]
    for p in produtos:
        client.post("/produtos", json=p)

    response = client.get("/produtos")
    assert response.status_code == 200
    assert len(response.json()) == 3
