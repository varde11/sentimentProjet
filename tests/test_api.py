import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db import get_db
from structure_table import Client, Produit, Prediction, Base

# in-memory sqlite engine reused across sessions; we'll recreate schema per test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # necessary for SQLite
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# helper used by fixtures to bootstrap a fresh schema and seed data

def _init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # always add at least one client and two products
    fake_client = Client(nom="varde", langue="FR")
    fake_produit1 = Produit(lien="photo/lunette.png", detail="Lunette pour être intélligent!")
    fake_produit2 = Produit(lien="photo/manga.png", detail="The seraph of the end!")
    db.add_all([fake_client, fake_produit1, fake_produit2])
    db.commit()
    db.close()


@pytest.fixture

def client():
    """Get a TestClient with a fresh in‑memory database for each test."""
    _init_db()
    with TestClient(app) as c:
        yield c


# --------- client related tests ---------

def test_client_crud(client):
    # get existing (id 1 inserted by fixture)
    resp = client.get("/GetClient/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nom"] == "varde"

    # add a new client
    resp = client.post("/AddClient/vava/eN")
    assert resp.status_code == 200
    assert resp.json()["langue"] == "EN"
    assert resp.json()["nom"] == "vava"

    # get all clients should return 2 entries
    resp = client.get("/GetAllClient")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # delete the second client and ensure 404 afterwards
    assert client.delete("/DeleteClient/2").status_code == 200
    assert client.get("/GetClient/2").status_code == 404


def test_get_all_client_empty_after_deletion(client):
    # delete the only pre‑existing client
    assert client.delete("/DeleteClient/1").status_code == 200
    # get all should still return [] or raise 500? per API it raises 500 if no clients
    resp = client.get("/GetAllClient")
    assert resp.status_code in (200, 500)


# --------- produit related tests ---------

def test_produit_endpoints(client):
    resp = client.get("/GetProduit/1")
    assert resp.status_code == 200
    assert "Lunette" in resp.json()["detail"]

    resp = client.get("/GetAllProduit")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --------- prediction tests (public, no client required) ---------

def _create_prediction(client, produit_id: int, avis: str):
    return client.post("/PredictPublic", json={"id_produit": produit_id, "avis": avis})


def test_prediction_public_and_fetch(client):
    # create a prediction without specifying id_client
    resp = _create_prediction(client, 1, "Ces lunettes sont superbe!")
    assert resp.status_code == 200
    pred = resp.json()
    assert pred["id_prediction"] == 1
    assert pred["id_client"] is None
    assert pred["id_produit"] == 1

    # fetch it by its id
    resp2 = client.get(f"/GetPredictionByIdPrediction/{pred['id_prediction']}")
    assert resp2.status_code == 200
    assert resp2.json()["avis"] == "Ces lunettes sont superbe!"

    # querying by client should return 404 because id_client is None
    assert client.get("/GetPredictionByIdClient/1").status_code == 404

    # querying by produit should return our single element
    resp3 = client.get("/GetPredictionByIdProduit/1")
    assert resp3.status_code == 200
    assert len(resp3.json()) == 1

    # /GetAllPredictions?label=all should include one prediction
    resp4 = client.get("/GetAllPredictions?label=all")
    assert resp4.status_code == 200
    assert len(resp4.json()) == 1


def test_prediction_deletions(client):
    # create two predictions
    _create_prediction(client, 1, "A")
    _create_prediction(client, 2, "B")

    # delete first by id
    assert client.delete("/DeletePredictionByIdPrediction/1").status_code == 200
    assert client.get("/GetPredictionByIdPrediction/1").status_code == 404

    # delete remaining by produit
    assert client.delete("/DeletePredictionByIdProduit/2").status_code == 200
    # nothing left
    resp = client.get("/GetAllPredictions?label=all")
    assert resp.status_code == 404 or len(resp.json()) == 0

    # deleting again returns 404
    assert client.delete("/DeletePredictionByIdProduit/2").status_code == 404


def test_predictions_for_nonexistent_client_returns_404(client):
    # no predictions at all yet
    assert client.get("/GetPredictionByIdClient/99").status_code == 404


# the fixture ensures each test starts with a clean DB, so tests remain independent
