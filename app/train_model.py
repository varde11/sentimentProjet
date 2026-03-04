import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "train_reviews.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "TF_LR.pkl")

label_map = {"negative": 0, "neutral": 1, "positive": 2}

df = pd.read_csv(DATA_PATH)
df["label_id"] = df["label"].map(label_map)

X = df["text"]
y = df["label_id"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# use a hashing vectorizer so that the feature space is fixed and
# we can safely update the classifier with new examples only
pipeline = Pipeline([
    ("hash", HashingVectorizer(
        ngram_range=(1, 2),
        alternate_sign=False,  # keep positive features
        n_features=2**20
    )),
    ("clf", SGDClassifier(
        loss="log",      # logistic regression
        max_iter=1000,
        tol=1e-3,
        warm_start=True   # allow successive calls to fit/partial_fit
    ))
])

# track how many rows of the CSV have already been used to train
count_path = MODEL_PATH + ".count"

if os.path.exists(MODEL_PATH) and os.path.exists(count_path):
    # load existing model and only fit on new samples
    pipeline = joblib.load(MODEL_PATH)
    prev_n = int(open(count_path).read().strip())
    if prev_n < len(X):
        X_new = X.iloc[prev_n:]
        y_new = y.iloc[prev_n:]
        # partial_fit requires classes on first call
        pipeline.named_steps["clf"].partial_fit(pipeline.named_steps["hash"].transform(X_new), y_new, classes=[0,1,2])
        print(f"Updated model with {len(X_new)} new examples")
    else:
        print("No new data to train on; model left unchanged.")
else:
    # first-time training on the full dataset
    pipeline.fit(X, y)
    print("Trained new model on entire dataset")

# save model and update count
joblib.dump(pipeline, MODEL_PATH)
with open(count_path, "w") as f:
    f.write(str(len(X)))
print("Model saved to:", MODEL_PATH)
