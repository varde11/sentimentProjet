from schema import ClientOut_schema,ProduitOut_schema,PredictionOut_schema,PredictionIn_schema,EnumLabel,FinalLabel
from schema import  MonitoringOut, IncidentOut, QueueItemOut, PopularProductOut,PredictPublicIn
import os
from structure_table import Client,Produit,Prediction,Base
from fill_db import seed_products_if_empty
from logic import load_artificats, predict_final
from db import get_db,engine,sessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func,select
from datetime import datetime
from fastapi import FastAPI,Depends,HTTPException,Query
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from datetime import datetime,timedelta

from typing import List, Dict, Any
import base64






@asynccontextmanager
async def lifespan(app:FastAPI):
    print("préparation des ressources!")
    Base.metadata.create_all(bind=engine)
    load_artificats()
    
    db = sessionLocal()
    try:
        seed_products_if_empty(db)
    finally:
        db.close()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    os.makedirs(STATIC_DIR, exist_ok=True) 
    
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print("préparation terminée")
    yield
    print("fermeture de l'application, merci de l'avoir essayer, a+")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="API sentiment",lifespan=lifespan)

@app.get("/GetHealthy")
def get_healthy():
    return {"healthy":"okayyyy"}


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

@app.get("/GetAllProduit", response_model=list[ProduitOut_schema])
def get_all_produit(db: Session = Depends(get_db)):
    produits = db.query(Produit).all()
    result = []
    for p in produits:
        img_path = os.path.join(BASE_DIR, "static", p.lien)
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = p.lien.rsplit(".", 1)[-1].lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
            lien = f"data:{mime};base64,{b64}"
        except FileNotFoundError:
            lien = ""
        result.append({"id_produit": p.id_produit, "lien": lien, "detail": p.detail})
    return result


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
        return []
    
    return predictions


@app.post("/Predict",response_model=PredictionOut_schema)
def predict_sentiment (pred:PredictionIn_schema,db:Session=Depends(get_db)):

    if not db.query(Client).filter(Client.id_client==pred.id_client).first():
        raise HTTPException(status_code=404,detail=f"Le client d'identifiant {pred.id_client} n'existe pas.")
    
    if not db.query(Produit).filter(Produit.id_produit==pred.id_produit).first():
        raise HTTPException(status_code=404,detail=f"Le produit d'identifiant {pred.id_produit} n'existe pas.")

    predict = predict_final([pred.avis])
    
    prediction = Prediction(
        id_client = pred.id_client,
        id_produit = pred.id_produit,
        avis = pred.avis,
        label = predict["label"],
        confidence = predict["confidence"],
        model =  predict["model"],
        scores = predict["scores"],
        time_stamp = datetime.now().replace(microsecond=0)
    )
    # ajoute un bloc pour vérifie que le client et le produit existe bien, peut être un try au  niveau de db.add
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction 




@app.post("/PredictPublic",response_model=PredictionOut_schema)
def predict_sentiment (pred:PredictPublicIn,db:Session=Depends(get_db)):

    
    if not db.query(Produit).filter(Produit.id_produit==pred.id_produit).first():
        raise HTTPException(status_code=404,detail=f"Le produit d'identifiant {pred.id_produit} n'existe pas.")

    predict = predict_final([pred.avis])
    
    prediction = Prediction(
        id_client = None,
        id_produit = pred.id_produit,
        avis = pred.avis,
        label = predict["label"],
        confidence = predict["confidence"],
        model =  predict["model"],
        scores = predict["scores"],
        time_stamp = datetime.now().replace(microsecond=0)
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







CRITICAL_KEYWORDS = [
    "arnaque", "dangereux", "fraude", "risque", "explose", "cassée", "abîmée", "scam", "bug"
]

def contains_critical_keyword(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in CRITICAL_KEYWORDS)

def compute_priority(
    label: str,
    confidence: float,
    avis: str,
    is_popular_product: bool
) -> Dict[str, Any]:
    score = 0
    reasons = []

    
    if label == "negative":
        score += 3
        reasons.append("avis négatif")
    elif label == "uncertain":
        score += 1
        reasons.append("avis incertain (à vérifier)")

    
    if confidence >= 0.65:
        score += 2
        reasons.append("haute confiance")

    # Mots critiques
    if contains_critical_keyword(avis):
        score += 3
        reasons.append("mot-clé critique détecté")

    # Popularité produit
    if is_popular_product:
        score += 3
        reasons.append("produit populaire")

    # Mapping score -> priorité
    if score >= 7:
        prio = "P0"
    elif score >= 4:
        prio = "P1"
    else:
        prio = "P2"

    return {"priority": prio, "priority_score": score, "reasons": reasons}



def matched_keywords(text: str) -> list[str]:
    t = (text or "").lower()
    return sorted([k for k in CRITICAL_KEYWORDS if k in t])



@app.get("/MonitoringAlerts", response_model=MonitoringOut)
def monitoring_alerts(
    window_days: int = Query(7, ge=1, le=30),
    spike_factor: float = Query(2.0, ge=1.0, le=10.0),
    min_negative: int = Query(2, ge=1, le=50),
    top_k_popular: int = Query(5, ge=1, le=20),
    max_queue: int = Query(50, ge=1, le=200),
    queue_offset: int = Query(0, ge=0, le=100000),

    db: Session = Depends(get_db)
):
    
    now = datetime.now().replace(microsecond=0)

    start_last = now - timedelta(days=window_days)
    start_prev = now - timedelta(days=2 * window_days)

    rows = (
        db.query(Prediction)
        .filter(Prediction.time_stamp >= start_prev)
        .limit(5000)
        .all()
    )

    if not rows:
        return MonitoringOut(
            window_days=window_days,
            generated_at=now,
            popular_products=[],
            incidents=[],
            review_queue=[],
        )

    # 2) Agrégation en mémoire (simple et efficace sur dataset 200-1000 lignes)
    #    On groupe par produit et par fenêtre.
    by_prod = {}
    for r in rows:
        pid = int(r.id_produit)
        by_prod.setdefault(pid, {"last": [], "prev": []})
        if r.time_stamp >= start_last:
            by_prod[pid]["last"].append(r)
        else:
            by_prod[pid]["prev"].append(r)

    # 3) Popularité : top produits par volume last_7d
    popular_stats: List[PopularProductOut] = []
    volume_list = []
    for pid, grp in by_prod.items():
        last = grp["last"]
        if not last:
            continue

        counts = {"positive": 0, "negative": 0, "neutral": 0, "uncertain": 0}
        for r in last:
            lbl = (r.label or "").lower()
            if lbl in counts:
                counts[lbl] += 1

        total = len(last)
        volume_list.append((pid, total, counts))

    volume_list.sort(key=lambda x: x[1], reverse=True)
    top_pop = volume_list[:top_k_popular]
    popular_set = {pid for pid, _, _ in top_pop}

    for pid, total, counts in top_pop:
        popular_stats.append(PopularProductOut(
            id_produit=pid,
            total_reviews_7d=total,
            positive_7d=counts["positive"],
            negative_7d=counts["negative"],
            neutral_7d=counts["neutral"],
            uncertain_7d=counts["uncertain"],
        ))

    # 4) Incidents : volume spike + keyword severity
    incidents: List[IncidentOut] = []

    for pid, grp in by_prod.items():
        last = grp["last"]
        prev = grp["prev"]

        neg_last = sum(1 for r in last if (r.label or "").lower() == "negative")
        neg_prev = sum(1 for r in prev if (r.label or "").lower() == "negative")

        # Spike (avec garde-fou min_negative)
        if neg_last >= min_negative and neg_last >= max(1, int(neg_prev * spike_factor)):
            
            neg_samples = [
                {
                    "id_prediction": c.id_prediction,
                    "avis": (c.avis or "")[:120],
                    "label": c.label,
                    "confidence": float(c.confidence or 0.0),
                    "time_stamp": c.time_stamp,
                }
                for c in last if (c.label or "").lower() == "negative"
                 ][-2:]  
            

            ratio = round(neg_last / max(1, neg_prev), 2)
            delta = neg_last - neg_prev

            details = {
                "neg_last_window": neg_last,
                "neg_prev_window": neg_prev,
                "delta": delta,
                "ratio": ratio,
                "spike_factor": spike_factor,
                "is_popular": pid in popular_set,
                "sample_predictions": neg_samples,
            }


            incidents.append(IncidentOut(
                type="volume_spike",
                id_produit=pid,
                title=f"Pic de négatifs détecté sur produit #{pid}",
                severity="P0" if pid in popular_set else "P1",
                details=details,
                time_window_days=window_days
            ))

        
        # Keyword severity (si au moins un avis contient un mot critique sur last window)
        crit = [r for r in last if contains_critical_keyword(r.avis)]
        if crit:
            sev = "P0" if (pid in popular_set or any((c.label or "").lower() == "negative" for c in crit)) else "P1"
            
            examples = [(c.avis or "")[:120] for c in crit[:3]]

            # keywords réellement rencontrés
            kws = sorted({kw for c in crit for kw in matched_keywords(c.avis)})

            # 2 derniers avis négatifs (si tu veux aussi)
            neg_samples = [
                {
                    "id_prediction": c.id_prediction,
                    "avis": (c.avis or "")[:120],
                    "label": c.label,
                    "confidence": float(c.confidence or 0.0),
                    "time_stamp": c.time_stamp,
                }
                for c in last if (c.label or "").lower() == "negative"
            ][-2:]


            incidents.append(IncidentOut(
                type="keyword_severity",
                id_produit=pid,
                title=f"Mot-clé critique détecté sur produit #{pid}",
                severity=sev,
                details={
                    "count": len(crit),
                    "examples": examples,
                    "matched_keywords": kws,
                    "is_popular": pid in popular_set,
                    "sample_predictions": neg_samples
                },
                time_window_days=window_days
            ))





    # 5) Review queue priorisée : surtout negative/uncertain sur last window
    queue_candidates = []
    for pid, grp in by_prod.items():
        for r in grp["last"]:
            lbl = (r.label or "").lower()
            if lbl not in ["negative", "uncertain"]:
                continue

            pr = compute_priority(
                label=lbl,
                confidence=float(r.confidence or 0.0),
                avis=r.avis or "",
                is_popular_product=(pid in popular_set)
            )
            queue_candidates.append((pr["priority_score"], r, pr))

    queue_candidates.sort(key=lambda x: x[0], reverse=True)
    queue_candidates = queue_candidates[queue_offset: queue_offset + max_queue]

    review_queue: List[QueueItemOut] = []
    for score, r, pr in queue_candidates:
        review_queue.append(QueueItemOut(
            id_prediction=int(r.id_prediction),
            id_produit=int(r.id_produit),
            label=str(r.label),
            confidence=float(r.confidence or 0.0),
            model=str(r.model),
            avis=str(r.avis),
            time_stamp=r.time_stamp,
            priority=pr["priority"],
            priority_score=int(pr["priority_score"]),
            reasons=pr["reasons"]
        ))

    return MonitoringOut(
        window_days=window_days,
        generated_at=now,
        popular_products=popular_stats,
        incidents=incidents,
        review_queue=review_queue
    )