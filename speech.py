from io import BytesIO

def speak_bangla(text):
    try:
        from gtts import gTTS
        buf = BytesIO()
        gTTS(text=text, lang="bn").write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None
