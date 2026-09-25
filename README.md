# 🤟 Ishara — Bangla Sign Language Translator

Ishara is a deployable, AI-assisted prototype for Bangla Sign Language accessibility.

## What is included

- Bangla + English interface
- Registration and login
- Camera-based hand landmark extraction
- Trainable sign classifier using MediaPipe + Random Forest
- Bangla text output
- Optional Bengali voice output
- Translation history
- Dataset Lab for collecting labeled samples
- Model training inside the app
- Admin dashboard
- Streamlit Cloud-ready project structure

## Important competition note

No honest software project should claim “100% bugless” or “100% accurate” AI recognition without testing on a representative, independently annotated dataset.

The project therefore deliberately separates:
1. **Software readiness** — the app, database, camera pipeline and training workflow are implemented.
2. **Recognition accuracy** — depends on the quality and diversity of your Bangla Sign Language dataset.

For the national competition, collect expert-approved samples before the final demo.

## Quick start

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit.

## GitHub → Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload all project files.
3. In Streamlit Community Cloud, create a new app.
4. Select the repository and branch `main`.
5. Set the main file to `app.py`.
6. Deploy.

## First model training

1. Open Ishara.
2. Register/login.
3. Go to **Dataset Lab**.
4. Select a sign.
5. Capture 30–100 samples.
6. Repeat for every target sign.
7. Train/retrain the model.
8. Return to Translator.
9. Test with new camera images that were NOT used for training.

## Suggested competition vocabulary

Start with 10–20 expert-approved signs such as:
হ্যালো, ধন্যবাদ, হ্যাঁ, না, সাহায্য, আমি, তুমি, পানি, খাবার, ডাক্তার.

Do not assign labels from guesswork. Confirm the exact BSL meaning and execution with qualified sign-language users/experts.

## Architecture

Camera
→ MediaPipe hand landmarks
→ normalized feature vector
→ Random Forest classifier
→ Bangla text
→ Bengali TTS

The reverse direction is represented as a visual sign-card sequence in this MVP. A full reverse translator should use expert-created BSL video/animation assets or a validated sign-generation model.

## Roadmap for a national-level system

### Phase 1 — MVP
- Static signs
- One-hand landmark tracking
- Bangla output
- Dataset collection
- User history

### Phase 2 — Real BSL recognition
- Two-hand tracking
- Temporal video sequences
- LSTM/GRU/Transformer or temporal CNN
- Facial and body features
- Sentence segmentation
- Expert annotation
- Train/validation/test split by signer

### Phase 3 — Real-world deployment
- Mobile application
- Offline inference
- Hospital/education/service workflows
- Privacy controls
- Consent-based dataset governance
- Accessibility testing with deaf/signing communities

## Privacy

The default app stores translation metadata locally in SQLite. Do not collect identifiable video data without informed consent. For competition data collection, document consent, purpose, retention and access rules.
