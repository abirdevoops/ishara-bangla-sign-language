import streamlit as st

def render_sign_avatar(tokens, lang="English"):
    st.markdown("### 🤟 Sign representation")
    st.caption(
        "MVP representation: the words are mapped into a visual sign-card sequence. "
        "Replace this module with a 3D/2D BSL avatar after expert-approved sign assets are available."
    )
    if not tokens:
        return
    cols = st.columns(min(4, len(tokens)))
    for i, tok in enumerate(tokens):
        with cols[i % len(cols)]:
            st.markdown(
                f"<div style='border:1px solid #dbe7e5;border-radius:16px;"
                f"padding:18px;text-align:center;font-size:26px;background:#fbfffe'>"
                f"🤟<br><b>{tok}</b></div>",
                unsafe_allow_html=True
            )
