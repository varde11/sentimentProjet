from sqlalchemy import Column,Integer,String,DateTime,ForeignKey,Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON,TEXT


class Base(DeclarativeBase):
    pass

class Client(Base):
    __tablename__ = 'client'

    id_client = Column (Integer,primary_key=True,index=True,autoincrement=True)
    nom = Column (String,nullable=False)
    langue = Column (String)

class Produit (Base):
    __tablename__ = 'produit'

    id_produit = Column(Integer,primary_key=True,index=True,autoincrement=True)
    lien = Column(String,nullable=False)
    detail = Column(TEXT,nullable=False)

class Prediction (Base):
    __tablename__ = 'prediction'

    id_prediction = Column(Integer,primary_key=True,autoincrement=True,index=True)
    id_client = Column (Integer, ForeignKey("client.id_client"),nullable=False)
    id_produit = Column (Integer, ForeignKey("produit.id_produit"),nullable=False)
    avis = Column (TEXT,nullable=False)
    label = Column (String,nullable=False)
    confidence = Column (Float,nullable=False)
    model = Column (String,nullable=False)
    scores = Column(JSON,nullable=False)
    time_stamp = Column(DateTime,nullable=False)
