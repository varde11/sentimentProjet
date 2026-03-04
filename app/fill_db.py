import os
import pandas as pd
from sqlalchemy.orm import Session
from structure_table import Produit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_CSV_PATH = os.path.join(BASE_DIR, "data", "seed_produits.csv")

def seed_products_if_empty(db: Session):
    
    if db.query(Produit).first() is not None:
        return

    if not os.path.exists(SEED_CSV_PATH):
      
        print(f"[SEED] CSV introuvable: {SEED_CSV_PATH}")
        return

    df = pd.read_csv(SEED_CSV_PATH)

    objs = [Produit(**row) for row in df.to_dict(orient="records")]
    db.bulk_save_objects(objs)
    db.commit()
    print(f"[SEED] {len(objs)} produits insérés.")