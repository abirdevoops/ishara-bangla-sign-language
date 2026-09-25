import streamlit as st
from pathlib import Path
import sqlite3
import hashlib
import time
import base64
import io
import json

from gesture_engine import extract_landmarks, predict_gesture, train_model, save_sample
from speech import speak_bangla
from avatar import render_sign_avatar
from db import (
    init_db, create_user, authenticate_user, save_translation,
    get_history, get_stats, is_admin, seed_admin
)

st.set_page_config(
    page_title="Ishara — Bangla Sign Language Translator",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
seed_admin()

# ---------- Styling ----------
st.markdown("""
<style>
:root { --ishara: #00a884; }
.main .block-container { max-width: 1250px; padding-top: 1.2rem; }
.hero {
    padding: 28px 30px; border-radius: 22px;
    background: linear-gradient(135deg,#0b172a,#123c4a);
    color: white; margin-bottom: 18px;
}
.hero h1 { font-size: 44px; margin: 0; }
.hero p { font-size: 17px; opacity: .92; margin-top: 8px; }
.badge {
    display:inline-block; padding:6px 12px; border-radius:999px;
    background:#d8fff4; color:#08785f; font-weight:700; margin:3px;
}
.result {
    border: 1px solid #dbe7e5; border-radius: 18px; padding: 20px;
    background: #fbfffe;
}
.small { color:#637381; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Translator"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

def t(en, bn):
    return bn if st.session_state.get("lang") == "বাংলা" else en

if "lang" not in st.session_state:
    st.session_state.lang = "English"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🤟 Ishara")
    st.caption("Bangla Sign Language AI Prototype")
    st.session_state.lang = st.radio(
        "Language / ভাষা", ["English", "বাংলা"],
        index=0 if st.session_state.lang == "English" else 1
    )

    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        pages = [
            t("Translator", "অনুবাদক"),
            t("Dataset Lab", "ডেটাসেট ল্যাব"),
            t("History", "ইতিহাস"),
            t("About", "সম্পর্কে"),
        ]
        if is_admin(st.session_state.user):
            pages.append(t("Admin", "অ্যাডমিন"))
        selected = st.radio(t("Navigation", "নেভিগেশন"), pages)
        mapping = {
            "Translator":"Translator", "অনুবাদক":"Translator",
            "Dataset Lab":"Dataset Lab", "ডেটাসেট ল্যাব":"Dataset Lab",
            "History":"History", "ইতিহাস":"History",
            "About":"About", "সম্পর্কে":"About",
            "Admin":"Admin", "অ্যাডমিন":"Admin"
        }
        st.session_state.page = mapping[selected]
        if st.button(t("Logout", "লগআউট"), use_container_width=True):
            st.session_state.user = None
            st.session_state.last_result = None
            st.rerun()
    else:
        st.info(t(
            "Create an account to save your translation history.",
            "অনুবাদের ইতিহাস সংরক্ষণ করতে একটি অ্যাকাউন্ট তৈরি করুন।"
        ))

# ---------- Auth ----------
if not st.session_state.user:
    st.markdown("""
    <div class="hero">
      <h1>🤟 Ishara</h1>
      <p>AI-assisted Bangla Sign Language translation and dataset platform.</p>
      <span class="badge">Computer Vision</span>
      <span class="badge">Bangla UI</span>
      <span class="badge">Live Camera</span>
      <span class="badge">Dataset Builder</span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t("Login", "লগইন"))
        u = st.text_input(t("Username", "ইউজারনেম"), key="login_u")
        p = st.text_input(t("Password", "পাসওয়ার্ড"), type="password", key="login_p")
        if st.button(t("Login", "লগইন"), type="primary", use_container_width=True):
            if authenticate_user(u.strip(), p):
                st.session_state.user = u.strip()
                st.rerun()
            else:
                st.error(t("Invalid username or password.", "ইউজারনেম বা পাসওয়ার্ড ভুল।"))
    with c2:
        st.subheader(t("Create account", "অ্যাকাউন্ট তৈরি"))
        nu = st.text_input(t("New username", "নতুন ইউজারনেম"), key="new_u")
        np = st.text_input(t("New password", "নতুন পাসওয়ার্ড"), type="password", key="new_p")
        cp = st.text_input(t("Confirm password", "পাসওয়ার্ড নিশ্চিত করুন"), type="password", key="new_cp")
        if st.button(t("Register", "রেজিস্টার"), use_container_width=True):
            if not nu or len(np) < 6:
                st.warning(t("Use a username and a password of at least 6 characters.",
                             "ইউজারনেম দিন এবং কমপক্ষে ৬ অক্ষরের পাসওয়ার্ড ব্যবহার করুন।"))
            elif np != cp:
                st.error(t("Passwords do not match.", "পাসওয়ার্ড মিলছে না।"))
            elif create_user(nu.strip(), np):
                st.success(t("Account created. You can now log in.", "অ্যাকাউন্ট তৈরি হয়েছে। এখন লগইন করুন।"))
            else:
                st.error(t("Username already exists.", "এই ইউজারনেম আগে থেকেই আছে।"))
    st.stop()

# ---------- Translator ----------
if st.session_state.page == "Translator":
    st.markdown(f"""
    <div class="hero">
      <h1>🤟 Ishara</h1>
      <p>{t("Bangla Sign Language → Bangla text/voice",
             "বাংলা সাইন ল্যাঙ্গুয়েজ → বাংলা টেক্সট/ভয়েস")}</p>
      <span class="badge">AI-assisted</span>
      <span class="badge">Camera</span>
      <span class="badge">Explainable</span>
    </div>
    """, unsafe_allow_html=True)

    st.warning(t(
        "Competition/demo note: the default project is a trainable prototype. For genuine Bangla Sign Language recognition, collect your team's labeled samples in Dataset Lab and train the model before the final presentation.",
        "প্রতিযোগিতা/ডেমো নোট: এটি একটি trainable prototype। প্রকৃত বাংলা সাইন ল্যাঙ্গুয়েজ শনাক্তকরণের জন্য Dataset Lab-এ টিমের labeled sample সংগ্রহ করে final presentation-এর আগে model train করুন।"
    ))

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader(t("1. Capture a sign", "১. একটি sign capture করুন"))
        img = st.camera_input(t("Show your hand to the camera", "ক্যামেরার সামনে হাতের gesture দেখান"))
        if img:
            st.image(img, caption=t("Captured frame", "ধারণ করা ছবি"), use_container_width=True)
            if st.button(t("🔎 Translate sign", "🔎 Sign অনুবাদ করুন"), type="primary", use_container_width=True):
                with st.spinner(t("Analysing hand landmarks…", "Hand landmark বিশ্লেষণ হচ্ছে…")):
                    landmarks = extract_landmarks(img.getvalue())
                    if landmarks is None:
                        st.error(t("No clear hand detected. Improve lighting and keep one hand inside the frame.",
                                   "হাত পরিষ্কারভাবে শনাক্ত হয়নি। আলো বাড়ান এবং একটি হাত frame-এর মধ্যে রাখুন।"))
                    else:
                        result = predict_gesture(landmarks)
                        st.session_state.last_result = result
                        save_translation(st.session_state.user, result["label_bn"], result["confidence"])
                        st.rerun()

    with right:
        st.subheader(t("2. Translation", "২. অনুবাদ"))
        r = st.session_state.last_result
        if r:
            st.markdown('<div class="result">', unsafe_allow_html=True)
            st.metric(t("Detected sign", "শনাক্ত sign"), r["label_bn"])
            st.metric(t("Confidence", "বিশ্বাসযোগ্যতা"), f'{r["confidence"]*100:.1f}%')
            st.progress(min(max(r["confidence"],0),1))
            st.caption(t(
                "Confidence is model confidence, not a guarantee of correctness.",
                "Confidence model-এর অনুমান; এটি সঠিকতার গ্যারান্টি নয়।"
            ))
            if st.button(t("🔊 Speak Bengali", "🔊 বাংলা voice"), use_container_width=True):
                audio = speak_bangla(r["label_bn"])
                if audio:
                    st.audio(audio, format="audio/mp3")
                else:
                    st.info(t("Voice service unavailable. Text result is still available.",
                              "Voice service পাওয়া যাচ্ছে না। Text result ব্যবহার করা যাবে।"))
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info(t("Your translated sign will appear here.", "আপনার অনুবাদ এখানে দেখা যাবে।"))

    st.divider()
    st.subheader(t("Reverse communication: Bengali → Sign representation",
                    "উল্টো যোগাযোগ: বাংলা → Sign representation"))
    text_in = st.text_input(t("Enter Bengali text", "বাংলা বাক্য লিখুন"),
                             placeholder="আমি সাহায্য চাই")
    if text_in:
        tokens = [x for x in text_in.strip().split() if x]
        render_sign_avatar(tokens[:12], lang=st.session_state.lang)

# ---------- Dataset Lab ----------
elif st.session_state.page == "Dataset Lab":
    st.title(t("🧪 Dataset Lab", "🧪 ডেটাসেট ল্যাব"))
    st.write(t(
        "This is the part that turns the prototype into a real competition system: collect labeled examples from your target Bangla Sign Language vocabulary, then train the classifier.",
        "এই অংশটি prototype-কে বাস্তব competition system-এ রূপ দেয়: নির্ধারিত বাংলা সাইন ল্যাঙ্গুয়েজ vocabulary-এর labeled example সংগ্রহ করুন এবং classifier train করুন।"
    ))
    labels = {
        "হ্যালো":"HELLO", "ধন্যবাদ":"THANK_YOU", "হ্যাঁ":"YES",
        "না":"NO", "সাহায্য":"HELP", "আমি":"I", "তুমি":"YOU",
        "পানি":"WATER", "খাবার":"FOOD", "ডাক্তার":"DOCTOR"
    }
    bn = st.selectbox(t("Choose label", "Label নির্বাচন করুন"), list(labels.keys()))
    st.caption(f'Internal label: `{labels[bn]}`')
    sample_img = st.camera_input(t("Capture training sample", "Training sample capture করুন"), key="dataset_cam")
    if sample_img:
        if st.button(t("➕ Save labeled sample", "➕ Labeled sample সংরক্ষণ করুন"), use_container_width=True):
            lm = extract_landmarks(sample_img.getvalue())
            if lm is None:
                st.error(t("No hand detected.", "হাত শনাক্ত হয়নি।"))
            else:
                path = save_sample(lm, labels[bn])
                st.success(t(f"Sample saved for {bn}.", f"{bn}-এর sample সংরক্ষিত হয়েছে।"))
    st.info(t(
        "Recommended: collect 30–100 samples per sign from multiple angles, distances and people. Keep the label definitions consistent.",
        "পরামর্শ: প্রতিটি sign-এর ৩০–১০০টি sample বিভিন্ন angle, distance ও মানুষের কাছ থেকে সংগ্রহ করুন। Label-এর সংজ্ঞা consistent রাখুন।"
    ))
    if st.button(t("🧠 Train / retrain model", "🧠 Model train/retrain করুন"), type="primary"):
        result = train_model()
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])

# ---------- History ----------
elif st.session_state.page == "History":
    st.title(t("📜 Translation history", "📜 অনুবাদের ইতিহাস"))
    rows = get_history(st.session_state.user)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(t("No translations yet.", "এখনও কোনো translation নেই।"))

# ---------- Admin ----------
elif st.session_state.page == "Admin":
    if not is_admin(st.session_state.user):
        st.error("Access denied.")
        st.stop()
    st.title("🛡️ Admin dashboard")
    stats = get_stats()
    a,b,c = st.columns(3)
    a.metric("Users", stats["users"])
    b.metric("Translations", stats["translations"])
    c.metric("Training samples", stats["samples"])
    st.write("The dashboard is intentionally lightweight for competition demonstration.")

# ---------- About ----------
elif st.session_state.page == "About":
    st.title(t("About Ishara", "Ishara সম্পর্কে"))
    st.markdown("""
    **Ishara** is an AI-assisted accessibility platform designed around Bangla Sign Language.

    **Core pipeline:** Camera → hand landmark extraction → trained classifier → Bangla text → optional Bengali speech.

    **Important scientific limitation:** sign language is not simply a collection of static hand shapes. Real-world Bangla Sign Language can involve motion, both hands, facial expression, body posture, context and sentence-level grammar. This project therefore provides a strong, deployable MVP architecture and a dataset/training workflow, rather than claiming that a small static classifier already understands the full language.

    **Competition roadmap:** expand from static signs to temporal video recognition, two-hand tracking, facial/body features, language modeling, and a curated Bangla Sign Language dataset with consent and expert annotation.
    """)
