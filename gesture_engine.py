from pathlib import Path
import pickle
import numpy as np
import cv2
import mediapipe as mp
from sklearn.ensemble import RandomForestClassifier

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
MODEL_PATH = BASE / "model.pkl"

mp_hands = mp.solutions.hands

# Bangla display labels for the initial vocabulary.
LABEL_BN = {
    "HELLO":"হ্যালো", "THANK_YOU":"ধন্যবাদ", "YES":"হ্যাঁ", "NO":"না",
    "HELP":"সাহায্য", "I":"আমি", "YOU":"তুমি", "WATER":"পানি",
    "FOOD":"খাবার", "DOCTOR":"ডাক্তার"
}

def _vector_from_hand(hand):
    # Normalize coordinates relative to wrist and scale by max distance.
    pts = np.array([[lm.x,lm.y,lm.z] for lm in hand.landmark], dtype=np.float32)
    pts = pts - pts[0]
    scale = np.max(np.linalg.norm(pts[:,:2], axis=1))
    if scale < 1e-6:
        scale = 1.0
    pts = pts / scale
    return pts.flatten()

def extract_landmarks(image_bytes):
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp_hands.Hands(
        static_image_mode=True, max_num_hands=1,
        min_detection_confidence=0.55
    ) as hands:
        res = hands.process(img_rgb)
    if not res.multi_hand_landmarks:
        return None
    return _vector_from_hand(res.multi_hand_landmarks[0])

def sample_count():
    total = 0
    for p in DATA.glob("*.npz"):
        try:
            total += len(np.load(p)["X"])
        except Exception:
            pass
    return total

def save_sample(vector, label):
    path = DATA / f"{label}.npz"
    if path.exists():
        old = np.load(path)
        X, y = list(old["X"]), list(old["y"])
    else:
        X, y = [], []
    X.append(vector)
    y.append(label)
    np.savez_compressed(path, X=np.asarray(X,dtype=np.float32), y=np.asarray(y))
    return path

def train_model():
    xs, ys = [], []
    for p in DATA.glob("*.npz"):
        try:
            z = np.load(p)
            if len(z["X"]):
                xs.extend(z["X"])
                ys.extend(z["y"])
        except Exception:
            continue
    if len(set(ys)) < 2:
        return {"ok":False,"message":"Collect samples for at least 2 different signs before training."}
    clf = RandomForestClassifier(
        n_estimators=250, random_state=42, class_weight="balanced_subsample"
    )
    clf.fit(np.asarray(xs), np.asarray(ys))
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    return {"ok":True,"message":f"Model trained with {len(ys)} samples across {len(set(ys))} labels."}

def _heuristic(vector):
    # Safe fallback for a first-run UI demo: it reports a generic gesture
    # rather than pretending that an untrained model is a validated BSL model.
    return {"label":"UNKNOWN", "label_bn":"অনির্ধারিত gesture", "confidence":0.0}

def predict_gesture(vector):
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH,"rb") as f:
                clf = pickle.load(f)
            proba = clf.predict_proba([vector])[0]
            idx = int(np.argmax(proba))
            label = str(clf.classes_[idx])
            conf = float(proba[idx])
            return {
                "label":label,
                "label_bn":LABEL_BN.get(label,label),
                "confidence":conf
            }
        except Exception:
            pass
    return _heuristic(vector)
