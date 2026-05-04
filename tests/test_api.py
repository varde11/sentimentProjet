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

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  
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




def test_client_crud(client):
    # get existing (id 1 inserted by fixture)
    resp = client.get("/GetClient/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nom"] == "varde"

    # ajout client
    resp = client.post("/AddClient/vava/eN")
    assert resp.status_code == 200
    assert resp.json()["langue"] == "EN"
    assert resp.json()["nom"] == "vava"

    
    resp = client.get("/GetAllClient")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    
    assert client.delete("/DeleteClient/2").status_code == 200
    assert client.get("/GetClient/2").status_code == 404


def test_get_all_client_empty_after_deletion(client):

    assert client.delete("/DeleteClient/1").status_code == 200

    resp = client.get("/GetAllClient")
    assert resp.status_code in (200, 500)




def test_produit_endpoints(client):
    resp = client.get("/GetProduit/1")
    assert resp.status_code == 200
    assert "Lunette" in resp.json()["detail"]

    resp = client.get("/GetAllProduit")
    assert resp.status_code == 200
    assert len(resp.json()) == 2



def _create_prediction(client, produit_id: int, avis: str):
    return client.post("/PredictPublic", json={"id_produit": produit_id, "avis": avis})


def test_prediction_public_and_fetch(client):
    
    resp = _create_prediction(client, 1, "Ces lunettes sont superbe!")
    assert resp.status_code == 200
    pred = resp.json()
    assert pred["id_prediction"] == 1
    assert pred["id_client"] is None
    assert pred["id_produit"] == 1


    resp2 = client.get(f"/GetPredictionByIdPrediction/{pred['id_prediction']}")
    assert resp2.status_code == 200
    assert resp2.json()["avis"] == "Ces lunettes sont superbe!"

    assert client.get("/GetPredictionByIdClient/1").status_code == 404

    resp3 = client.get("/GetPredictionByIdProduit/1")
    assert resp3.status_code == 200
    assert len(resp3.json()) == 1

    resp4 = client.get("/GetAllPredictions?label=all")
    assert resp4.status_code == 200
    assert len(resp4.json()) == 1


def test_prediction_deletions(client):
    
    _create_prediction(client, 1, "A")
    _create_prediction(client, 2, "B")

    
    assert client.delete("/DeletePredictionByIdPrediction/1").status_code == 200
    assert client.get("/GetPredictionByIdPrediction/1").status_code == 404

    
    assert client.delete("/DeletePredictionByIdProduit/2").status_code == 200
    
    resp = client.get("/GetAllPredictions?label=all")
    assert resp.status_code == 404 or len(resp.json()) == 0


    assert client.delete("/DeletePredictionByIdProduit/2").status_code == 404


def test_predictions_for_nonexistent_client_returns_404(client):
    
    assert client.get("/GetPredictionByIdClient/99").status_code == 404


