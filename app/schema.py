from pydantic import BaseModel,Field
from typing import Literal,List,Optional,Dict,Any
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
    id_client : Optional[int] = None
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

class PredictPublicIn(BaseModel):
    id_produit: int = Field(ge=1)
    avis: str = Field(min_length=1, max_length=2000)

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




Priority = Literal["P0", "P1", "P2"]
IncidentType = Literal["volume_spike", "keyword_severity"]

class IncidentOut(BaseModel):
    type: IncidentType
    id_produit: int
    title: str
    severity: Priority
    details: Dict[str, Any] = {}
    sample_prediction: List[dict] = None
    time_window_days: int = 7

class QueueItemOut(BaseModel):
    id_prediction: int
    id_produit: int
    label: str
    confidence: float
    model: str
    avis: str
    time_stamp: datetime
    priority: Priority
    priority_score: int
    reasons: List[str] = []

class PopularProductOut(BaseModel):
    id_produit: int
    total_reviews_7d: int
    positive_7d: int
    negative_7d: int
    neutral_7d: int
    uncertain_7d: int

class MonitoringOut(BaseModel):
    window_days: int = 7
    generated_at: datetime
    popular_products: List[PopularProductOut]
    incidents: List[IncidentOut]
    review_queue: List[QueueItemOut]
