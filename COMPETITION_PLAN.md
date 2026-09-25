# Ishara — National Competition Demo Plan

## 3-minute live demo

**0:00–0:30 — Problem**
Show a communication barrier scenario in a hospital/service desk.

**0:30–1:15 — Sign → Bangla**
Open Translator → camera → show a trained sign → Translate → Bangla text → optional voice.

**1:15–1:45 — Explainable AI**
Show confidence and explain that the classifier was trained on your team's labeled BSL dataset.

**1:45–2:15 — Dataset Lab**
Show how a new sign sample is captured and added to the dataset.

**2:15–2:40 — Reverse direction**
Type a Bengali phrase and show the current visual sign-card representation.

**2:40–3:00 — Impact**
Explain future extension to hospitals, education, banks, government services and emergency communication.

## What judges should see

- Working camera pipeline
- A real trained model
- A dataset created by your team
- Measured test accuracy
- Error examples
- Clear limitations
- Privacy/consent process
- A realistic roadmap to temporal BSL recognition

## Do not claim

- Full Bangla Sign Language understanding
- 100% accuracy
- Universal sign-language coverage
- Automatic expert-level translation

unless independently demonstrated with appropriate evaluation.

## Evaluation protocol

Split data by signer, not just by random frames. Otherwise the model can memorize a person's hand appearance.

Report:
- Number of signs
- Number of signers
- Number of samples
- Train/validation/test counts
- Accuracy
- Macro F1
- Confusion matrix
- Inference latency
- Failure cases

A signer-independent test set is especially important for a credible competition claim.
