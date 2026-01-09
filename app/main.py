from schema import ClientOut_schema,ProduitOut_schema,PredictionOut_schema,PredictionIn_schema,EnumLabel,FinalLabel
import os
from structure_table import Client,Produit,Prediction,Base
from logic import load_artificats, predict_final
from db import get_db,engine
from sqlalchemy.orm import Session
from sqlalchemy import func,select
from datetime import datetime
from fastapi import FastAPI,Depends,HTTPException
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from datetime import datetime


@asynccontextmanager
async def lifespan(app:FastAPI):
    print("préparation des ressources!")
    Base.metadata.create_all(bind=engine)
    load_artificats()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    os.makedirs(STATIC_DIR, exist_ok=True) 
    
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print("préparation terminée")
    yield
    print("fermeture de l'application, merci de l'avoir essayer, a+")


app = FastAPI(title="API sentiment",lifespan=lifespan)


@app.get("/GetClient/{id_client}",response_model=ClientOut_schema)
def get_client_by_id(id_client:int,db:Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id_client==id_client).first()
    if not client:
        raise HTTPException(status_code=404,detail=f"Client d'identifiant {id_client} introuvable.")
    return client


@app.get("/GetAllClient",response_model=list[ClientOut_schema])
def get_all_client(db:Session=Depends(get_db)):
    clients = db.query(Client).all()
    if not clients :
        raise HTTPException(status_code=500,detail="Something went wrong, contact varde for more information.")
    return clients


@app.get("/GetProduit/{id_produit}",response_model=ProduitOut_schema)
def get_produit_by_id(id_produit:int,db:Session = Depends(get_db)):
    produit = db.query(Produit).filter(Produit.id_produit == id_produit).first()
    if not produit:
        raise HTTPException(status_code=404,detail=f"Produit d'identifiant {id_produit} introuvable.")
    
    return {"id_produit":produit.id_produit,
            "lien": f"{os.getenv('BASE_URL')}/static/{produit.lien}",
            "detail" : produit.detail
        }


@app.get("/GetAllProduit",response_model=list[ProduitOut_schema])
def get_all_produit(db:Session=Depends(get_db)):
    
    query = select(
    Produit.id_produit,
    func.concat(f"{os.getenv('BASE_URL')}/static/", Produit.lien).label('lien'),
    Produit.detail
    )

    produits = db.execute(query).fetchall()
   
    if not produits :
        raise HTTPException(status_code=500,detail="Something went wrong, contact varde for more information.")
    
    return produits


@app.get("/GetPredictionByIdPrediction/{id_prediction}",response_model=PredictionOut_schema)
def get_prediction_by_idPrediction(id_prediction:int, db:Session = Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_prediction==id_prediction).first()

    if not prediction:
        raise HTTPException(status_code=404,detail=f"Prédiction d'identifiant {id_prediction} introuvable.")
    return prediction


@app.get("/GetPredictionByIdClient/{id_client}",response_model=list[PredictionOut_schema])
def get_prediction_by_idClient(id_client:int, db:Session = Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_client==id_client).all()

    if not prediction:
        raise HTTPException(status_code=404,detail=f"Prédiction du client d'identifiant {id_client} introuvable.")
    return prediction 


@app.get("/GetPredictionByIdProduit/{id_produit}",response_model=list[PredictionOut_schema])
def get_prediction_by_idClient(id_produit:int, db:Session = Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_produit==id_produit).all()

    if not prediction:
        raise HTTPException(status_code=404,detail=f"Prédiction du produit d'identifiant {id_produit} introuvable.")
    return prediction 


@app.get("/GetAllPredictions",response_model=list[PredictionOut_schema])
def get_prediction_by_label(label:EnumLabel,db:Session = Depends(get_db)):
    if label == "all":
        predictions = db.query(Prediction).all()
    else:
        predictions = db.query(Prediction).filter(Prediction.label==label).order_by(Prediction.time_stamp.desc()).all()
                                  
    
    if not predictions:
        raise HTTPException(status_code=404,detail=f"Aucune prédiction avec le label {label.value} trouvée")
    
    return predictions


@app.post("/Predict",response_model=PredictionOut_schema)
def predict_sentiment (pred:PredictionIn_schema,db:Session=Depends(get_db)):

    if not db.query(Client).filter(Client.id_client==pred.id_client).first():
        raise HTTPException(status_code=404,detail=f"Le client d'identifiant {pred.id_client} n'existe pas.")
    
    if not db.query(Produit).filter(Produit.id_produit==pred.id_produit).first():
        raise HTTPException(status_code=404,detail=f"Le produit d'identifiant {pred.id_produit} n'existe pas.")

    predict = predict_final([pred.avis])
    time_stamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prediction = Prediction(
        id_client = pred.id_client,
        id_produit = pred.id_produit,
        avis = pred.avis,
        label = predict["label"],
        confidence = predict["confidence"],
        model =  predict["model"],
        scores = predict["scores"],
        time_stamp = datetime.now().strptime(time_stamp_str,"%Y-%m-%d %H:%M:%S")
    )
    # ajoute un bloc pour vérifie que le client et le produit existe bien, peut être un try au  niveau de db.add
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction 

@app.post("/AddClient/{nom}/{langue}",response_model=ClientOut_schema)
def add_client(nom:str,langue:str,db:Session=Depends(get_db)):
    client =  Client(nom = nom,langue = langue.upper())
    db.add(client)
    db.commit()
    db.refresh(client)
    #upcase la langue pour avoir FR au lieu de Fr ou fR ou fr que le client va rentrer.
    return client

@app.delete("/DeleteClient/{id_client}")
def delete_client(id_client:int,db:Session=Depends(get_db)):

    client = db.query(Client).filter(Client.id_client==id_client).first()
    if not client :
        raise HTTPException(status_code=404,detail=f"Client d'identifiant {id_client} introuvable.")
    
    deleted = ClientOut_schema.model_validate(client).model_dump()

    db.query(Client).filter(Client.id_client==id_client).delete(synchronize_session=False)
    db.commit()
    
    return {"Client supprimé ":deleted}


@app.delete("/DeletePredictionByIdPrediction/{id_prediction}")
def delete_prediction_by_idPrediction(id_prediction:int,db:Session=Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_prediction==id_prediction).first()

    if not prediction :
        raise HTTPException(status_code=404,detail=f"Prediction d'identifiant {id_prediction} introuvable.")
    
    deleted = PredictionOut_schema.model_validate(prediction).model_dump()

    db.query(Prediction).filter(Prediction.id_prediction == id_prediction).delete(synchronize_session=False)
    db.commit()

    return {"Prediction supprimée":deleted}


@app.delete("/DeletePredictionByIdClient/{id_client}")
def delete_prediction_by_idClient(id_client:int , db: Session=Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_client==id_client).all()

    if not prediction :
        raise HTTPException(status_code=404,detail=f"Prediction du client d'identifiant {id_client} introuvable.")
    
    deleted = [PredictionOut_schema.model_validate(pred).model_dump() for pred in prediction]

    db.query(Prediction).filter(Prediction.id_client == id_client).delete(synchronize_session=False)
    db.commit()

    return {"Prediction(s) supprimée(s)":deleted}


@app.delete("/DeletePredictionByIdProduit/{id_produit}")
def delete_prediction_by_idProduit(id_produit:int, db: Session=Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_produit == id_produit).all()

    if not prediction :
        raise HTTPException(status_code=404,detail=f"Prediction sur le produit d'identifiant {id_produit} introuvable.")
    
    deleted = [PredictionOut_schema.model_validate(pred).model_dump() for pred in prediction]

    db.query(Prediction).filter(Prediction.id_produit == id_produit).delete(synchronize_session=False)
    db.commit()

    return {"Prediction(s) supprimée(s)":deleted}


@app.put("/UpdateLabel/{id_prediction}",response_model=PredictionOut_schema)
def update_label(id_prediction:int,label:FinalLabel,db:Session=Depends(get_db)):

    prediction = db.query(Prediction).filter(Prediction.id_prediction==id_prediction).first()
    if not prediction :
        raise HTTPException(status_code=404,detail=f"Prediction d'identifiant {id_prediction} introuvable.")
    if not prediction.label == "uncertain":
        raise HTTPException(status_code=422,detail=f"La prédiction d'identifiant {id_prediction} a déjà un label: {prediction.label}")
    
    prediction.label = label
    db.commit()
    db.refresh(prediction)

    return prediction

