from pydantic import BaseModel,Field
from typing import Literal
from datetime import datetime
from enum import Enum

class ClientOut_schema(BaseModel):
    id_client : int = Field(ge=1)
    nom : str 
    langue : str
    model_config = {"from_attributes": True}

class ProduitOut_schema (BaseModel):
    id_produit : int = Field(ge=1)
    lien : str 
    detail : str

class PredictionOut_schema (BaseModel):
    id_prediction : int = Field(ge=1)
    id_client : int = Field(ge=1)
    id_produit : int = Field(ge=1)
    avis : str
    label : Literal ['negative','neutral','positive','uncertain']
    confidence : float = Field(ge=0,le=1)
    model : Literal ['TF_LR','XLM_R','not_used']
    scores : dict[str,float | dict[str,float] ]

    time_stamp : datetime

    model_config = {"from_attributes": True}

class PredictionIn_schema(BaseModel):
    id_client : int = Field (ge=1)
    id_produit : int = Field (ge=1)
    avis : str 

class EnumLabel(str,Enum):
    all = "all"
    negative = "negative"
    neutral = "neutral"
    positive = "positive"
    uncertain = "uncertain"
    

class FinalLabel (str,Enum):
    negative = "negative"
    neutral = "neutral"
    positive = "positive"
