import asyncio, io, os
import streamlit as st
import edge_tts
from pydub import AudioSegment

st.set_page_config(page_title="Visualization Audio Maker", page_icon="🎧")
st.title("🎧 Visualization Audio Maker")

# ---------- VOICE CHOICES ----------
VOICES = {
    "English - Jenny (US, calm)": "en-US-JennyNeural",
    "English - Aria (US, warm)": "en-US-AriaNeural",
    "English - Ava (US, soft)": "en-US-AvaNeural",
    "English - Sonia (UK)": "en-GB-SoniaNeural",
    "English - Libby (UK)": "en-GB-LibbyNeural",
    "English - Natasha (Australia)": "en-AU-NatashaNeural",
    "English - Andrew (US, male)": "en-US-AndrewNeural",
    "English - Ryan (UK, male)": "en-GB-RyanNeural",
    "Tamil - Pallavi (India, female)": "ta-IN-PallaviNeural",
    "Tamil - Valluvar (India, male)": "ta-IN-ValluvarNeural",
    "Tamil - Saranya (Sri Lanka, female)": "ta-LK-SaranyaNeural",
    "Tamil - Venba (Singapore, female)": "ta-SG-VenbaNeural",
    "Tamil - Kani (Malaysia, female)": "ta-MY-KaniNeural",
}

# ---------- MUSIC CHOICES (every mp3/wav in the 'music' folder) ----------
MUSIC_DIR = "music"
os.makedirs(MUSIC_DIR, exist_ok=True)
tracks = sorted(f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav")))

script = st.text_area(
    "Your script (leave a blank line between paragraphs for a pause)", height=250
)
voice_name = st.selectbox("Voice", list(VOICES))
speed = st.slider("Speed (left = slower)", -50, 0, -20, format="%d%%")
pitch = st.slider("Pitch (left = deeper, right = higher)", -30, 20, -5, format="%d Hz")
st.caption("Tip: for Tamil voices, keep speed between -5% and -15%. Heavy slowing sounds unnatural.")
pause = st.slider("Pause between paragraphs (seconds)", 1, 10, 4)
music = st.selectbox("Background music", ["None"] + tracks)
music_vol = st.slider("Music volume (dB, lower is quieter)", -35, -10, -22)


async def speak(text, voice, rate, pitch, path):
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)


def build(script, voice, speed, pitch, pause, music, music_vol):
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    track = AudioSegment.silent(duration=3000)
    for i, p in enumerate(paragraphs):
        path = f"tmp_{i}.mp3"
        asyncio.run(speak(p, voice, f"{speed:+d}%", f"{pitch:+d}Hz", path))
        track += AudioSegment.from_file(path) + AudioSegment.silent(duration=pause * 1000)
        os.remove(path)
    track += AudioSegment.silent(duration=3000)

    if music != "None":
        bgm = AudioSegment.from_file(os.path.join(MUSIC_DIR, music))
        bgm = (bgm * (len(track) // len(bgm) + 1))[: len(track)]
        bgm = (bgm + music_vol).fade_in(3000).fade_out(5000)
        track = track.overlay(bgm)

    buf = io.BytesIO()
    track.export(buf, format="mp3")
    return buf.getvalue()


if st.button("Generate audio"):
    if not script.strip():
        st.warning("Please type or paste your script first.")
    else:
        try:
            with st.spinner("Creating your audio..."):
                audio = build(script, VOICES[voice_name], speed, pitch, pause, music, music_vol)
            st.audio(audio, format="audio/mp3")
            st.download_button("Download MP3", audio, "visualization.mp3", "audio/mp3")
        except Exception as e:
            st.error(f"Something went wrong (try another voice): {e}")
