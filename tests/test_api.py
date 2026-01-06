import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))


from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app 
from db import get_db
from structure_table import Client, Produit,Prediction,Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
load_dotenv()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Nécessaire pour SQLite
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def setup_database():
    Base.metadata.create_all(bind=engine)
    db =TestingSessionLocal()
    fake_client = Client(nom="varde",langue="FR")
    fake_produit1 = Produit(lien="photo/lunette.png",detail="Lunette pour être intélligent!")
    fake_produit2 = Produit(lien="photo/manga.png",detail="The seraph of the end!")
    db.add(fake_client)
    db.add(fake_produit1)
    db.add(fake_produit2)
    db.commit()
    db.close()


def test_mon_api():
    with TestClient(app) as client:
        setup_database()
        reponse_get_client = client.get("/GetClient/1")
        assert reponse_get_client.status_code == 200
        
        reponse_post_client = client.post("/AddClient/vava/eN")
        assert reponse_post_client.status_code == 200
        assert reponse_post_client.json()['langue'] == "EN"
        assert reponse_post_client.json()['nom'] == "vava"

        reponse_get_all_client = client.get("/GetAllClient")
        assert reponse_get_all_client.status_code == 200
        assert len(reponse_get_all_client.json()) == 2

        reponse_get_produit = client.get("/GetProduit/1")
        assert reponse_get_produit.status_code == 200
        assert reponse_get_produit.json()['lien'] == "http://localhost:8000/static/photo/lunette.png"
        assert reponse_get_produit.json()['detail'] == "Lunette pour être intélligent!"

        reponse_get_all_produit = client.get("/GetAllProduit")
        assert reponse_get_all_produit.status_code == 200
        assert len(reponse_get_all_produit.json()) == 2

        reponse_predict1 = client.post("/Predict",json={'id_client':1,'id_produit':1,'avis':"Ces lunettes sont superbe!"})
        reponse_predict2 = client.post("/Predict",json={'id_client':1,'id_produit':2,'avis':"Le manga est trop bien!"})
        reponse_predict3 = client.post("/Predict",json={'id_client':2,'id_produit':1,'avis':"Ces lunettes sont trop null!"})
        reponse_predict4 = client.post("/Predict",json={'id_client':2,'id_produit':2,'avis':"C'est null, le regardez pas!"})
        reponse_predict =[reponse_predict1,reponse_predict2,reponse_predict3,reponse_predict4]
        
        for rep in reponse_predict :
            assert rep.status_code == 200
        
        for id_pred in range(1,5):
            reponse_get_pred_idPred = client.get(f"/GetPredictionByIdPrediction/{id_pred}")
            assert reponse_get_pred_idPred.status_code == 200
        
        for id in range(1,3):
            reponse_get_pred_idClient = client.get(f"/GetPredictionByIdClient/{id}")
            reponse_get_pred_idProduit = client.get(f"/GetPredictionByIdPrediction/{id}")
            assert all([reponse_get_pred_idClient.status_code == 200, reponse_get_pred_idProduit.status_code == 200])
            assert all ([len(reponse_get_pred_idClient.json()) == 2, len(reponse_get_pred_idClient.json()) == 2 ])
        
        reponse_get_all_pred = client.get("/GetAllPredictions?label=all")
        assert reponse_get_all_pred.status_code == 200
        assert len(reponse_get_all_pred.json()) == 4 

        
        reponse_post_client = client.post("/AddClient/vardake/fR")
        assert reponse_post_client.status_code == 200

        reponse_delete_client = client.delete("/DeleteClient/3")
        assert reponse_delete_client.status_code == 200

        assert client.get("/GetClient/3").status_code == 404

        assert client.delete("/DeletePredictionByIdPrediction/1").status_code == 200
        assert client.get("/GetPredictionByIdPrediction/1").status_code == 404

        assert client.delete("/DeletePredictionByIdClient/1").status_code == 200
        assert client.get("/GetPredictionByIdClient/1").status_code == 404
        assert len(client.get("/GetAllPredictions?label=all").json()) ==  2
        
        assert client.delete("/DeletePredictionByIdProduit/1").status_code == 200
        assert len(client.get("/GetAllPredictions?label=all").json()) ==  1
        assert client.delete("/DeletePredictionByIdProduit/2").status_code == 200
        assert client.delete("/DeletePredictionByIdProduit/2").status_code == 404
        assert client.delete("/DeletePredictionByIdProduit/1").status_code == 404
        


    
            
    

    
        

        
        


        