import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


def _get(path: str, params: dict | None = None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, json: dict):
    r = requests.post(f"{API_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json()


def _put(path: str, params: dict | None = None, json: dict | None = None):
    r = requests.put(f"{API_URL}{path}", params=params, json=json, timeout=30)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=3600)
def get_all_produits():
    return _get("/GetAllProduit")

@st.cache_data(ttl=3600)
def get_produit(id_produit: int):
    return _get(f"/GetProduit/{id_produit}")

@st.cache_data(ttl=3600)
def get_all_clients():
    return _get("/GetAllClient")

@st.cache_data(ttl=20)
def get_predictions_by_produit(id_produit: int):
    # Si ton API renvoie 404 quand rien n'existe, on retourne []
    try:
        return _get(f"/GetPredictionByIdProduit/{id_produit}")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []
        raise


def get_predictions_by_client(id_client: int):
    try:
        return _get(f"/GetPredictionByIdClient/{id_client}")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []
        raise


def get_uncertain_predictions():
    return _get("/GetAllPredictions", params={"label": "uncertain"})


def predict(payload: dict):
    return _post("/Predict", json=payload)

def PredictPublic(payload:dict):
    return _post("/PredictPublic",json=payload)


def update_label(id_prediction: int, label: str):
    
    return _put(f"/UpdateLabel/{id_prediction}", params={"label": label})



from typing import Dict, Any

class ApiError(Exception):
    pass

def _handle(resp: requests.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
    except Exception:
        raise ApiError(f"Erreur API ({resp.status_code})")
    if resp.status_code >= 400:
        detail = data.get("detail") if isinstance(data, dict) else data
        raise ApiError(f"Erreur API ({resp.status_code}): {detail}")
    return data

def get_monitoring_alerts(params: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.get(f"{API_URL}/MonitoringAlerts", params=params, timeout=30)
    return _handle(resp)