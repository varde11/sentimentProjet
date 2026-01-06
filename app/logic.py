import joblib
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__) )
#XLMR_PATH = os.path.join(BASE_DIR,"model","xlmr_model")
XLMR_MODEL_ID = "varde11/sentiment_projet"
TFLR_PATH = os.path.join(BASE_DIR,"model","TF_LR.pkl")


global tflr_seuil,xlmr_seuil,labels

tflr_seuil = 0.2
xlmr_seuil = 0.2
labels = {"0" : "negative", "1" : "neutral", "2" : "positive"}

tokenizer = None
xlmr_model = None
tflr_model = None

def load_artificats():
    global tokenizer,xlmr_model,tflr_model

    if tokenizer == None:
        tokenizer = AutoTokenizer.from_pretrained(XLMR_MODEL_ID)
    if xlmr_model == None:
        xlmr_model = AutoModelForSequenceClassification.from_pretrained(XLMR_MODEL_ID)
        xlmr_model.eval()
    if tflr_model == None :
        tflr_model = joblib.load(str(TFLR_PATH))


def predict_from_tflr (text:list[str]):
    
    pred = tflr_model.predict_proba(text)
    

    pred_sort = np.sort(pred)
    label = labels[str(tflr_model.predict(text)[0])]
    confidence = float(round(pred_sort[0][2],3))
    scores = {'negative':float(round(pred[0][0],3)),'neutral': float(round(pred[0][1],3)), 'positive': float(round(pred[0][2],3))}

    
    if (pred_sort[0][2]-pred_sort[0][1]) >= tflr_seuil:
        return {"trust":True,"label":label,"confidence":confidence,"model":"TF_LR","scores":scores}

    else :
        return {"trust":False,"label":label,"confidence":confidence,"model":"TF_LR","scores":scores}


def predict_from_xlmr(text:list[str]):

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        outputs = xlmr_model(**inputs)          
    probs = F.softmax(outputs.logits, dim=-1).squeeze(0)  


    probs_np = probs.cpu().detach().numpy()
    probs_sort = np.sort(probs_np)  # array([0.1, 0.2, 0.7])
    label = labels[str(probs.argmax().item())]
    confidence = round(float(probs.max().item()),3)
    scores = {"negative": round(float(probs_np[0]), 3), "neutral": round(float(probs_np[1]), 3), "positive": round(float(probs_np[2]), 3)}

    if (probs_sort[-1] - probs_sort[-2]) >= xlmr_seuil:
        return {"trust": True, "label": label, "confidence": confidence, "model": "XLM_R", "scores": scores}
    else:
        return {"trust": False, "label": label, "confidence": confidence, "model": "XLM_R", "scores": scores}
    

def predict_final(text:list[str]):

    tflr_prediction = predict_from_tflr(text)
    
    if(tflr_prediction["trust"]):
        return tflr_prediction
    
    xlmr_prediction = predict_from_xlmr(text)

    if (xlmr_prediction["trust"]):
        return xlmr_prediction
    
    return {"label":"uncertain","confidence":max(xlmr_prediction["confidence"],tflr_prediction["confidence"]),
            "model": "not_used","scores":{"scores_tflr":tflr_prediction["scores"],"scores_xlmr":xlmr_prediction["scores"]}
            }


load_artificats()
print(predict_final(["Super le produit!"]))

#print("Base_DIR:",BASE_DIR,"\nXLMR:",XLMR_PATH,"\nTFLR_PATH:",TFLR_PATH)
