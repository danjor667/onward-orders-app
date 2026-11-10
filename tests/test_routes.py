import pytest

from app import config, create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_home_shows_owner_and_lab_name(client):
    page = client.get("/").get_data(as_text=True)
    assert config.OWNER_NAME in page
    assert config.LAB_NAME in page


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_order_from_form_then_see_it(client):
    response = client.post(
        "/orders", data={"merchant": "Shop", "customer": "Esi Boateng", "destination": "Tema"}
    )
    assert response.status_code == 302
    assert "Esi Boateng" in client.get("/").get_data(as_text=True)


def test_invalid_form_shows_error(client):
    response = client.post("/orders", data={"merchant": "Shop"})
    assert response.status_code == 400
    assert "Missing" in response.get_data(as_text=True)


def test_advance_order(client):
    assert client.post("/orders/2/advance").status_code == 302
    orders = {order["id"]: order for order in client.get("/api/orders").get_json()}
    assert orders[2]["status"] == "picked_up"


def test_api_create_and_validate(client):
    created = client.post(
        "/api/orders", json={"merchant": "Shop", "customer": "Ama", "destination": "Accra"}
    )
    assert created.status_code == 201
    assert created.get_json()["status"] == "received"
    assert client.post("/api/orders", json={"merchant": "Shop"}).status_code == 400


def test_user_input_is_escaped(client):
    client.post(
        "/orders",
        data={"merchant": "<script>alert(1)</script>", "customer": "Ama", "destination": "Accra"},
    )
    assert "<script>alert(1)</script>" not in client.get("/").get_data(as_text=True)
