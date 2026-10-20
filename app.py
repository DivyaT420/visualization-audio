import asyncio, io, os
import streamlit as st
import edge_tts
from pydub import AudioSegment

st.set_page_config(page_title="Visualization Audio Maker", page_icon="🎧")
st.title("🎧 Visualization Audio Maker")

# ---------- VOICE CHOICES (add more from: edge-tts --list-voices) ----------
VOICES = {
    "Jenny (English, US, calm)": "en-US-JennyNeural",
    "Aria (English, US, warm)": "en-US-AriaNeural",
    "Neerja (English, India)": "en-IN-NeerjaNeural",
    "Pallavi (Tamil, female)": "ta-IN-PallaviNeural",
    "Valluvar (Tamil, male)": "ta-IN-ValluvarNeural",
    "Swara (Hindi, female)": "hi-IN-SwaraNeural",
}

# ---------- MUSIC CHOICES (every mp3 in the 'music' folder) ----------
MUSIC_DIR = "music"
os.makedirs(MUSIC_DIR, exist_ok=True)
tracks = sorted(f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav")))

script = st.text_area(
    "Your script (leave a blank line between paragraphs for a pause)", height=250
)
voice_name = st.selectbox("Voice", list(VOICES))
speed = st.slider("Speed (slower is left)", -50, 0, -25, format="%d%%")
pause = st.slider("Pause between paragraphs (seconds)", 1, 10, 4)
music = st.selectbox("Background music", ["None"] + tracks)
music_vol = st.slider("Music volume (dB, lower is quieter)", -35, -10, -22)


async def speak(text, voice, rate, path):
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


def build(script, voice, speed, pause, music, music_vol):
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    track = AudioSegment.silent(duration=3000)
    for i, p in enumerate(paragraphs):
        path = f"tmp_{i}.mp3"
        asyncio.run(speak(p, voice, f"{speed:+d}%", path))
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
        with st.spinner("Creating your audio..."):
            audio = build(script, VOICES[voice_name], speed, pause, music, music_vol)
        st.audio(audio, format="audio/mp3")
        st.download_button("Download MP3", audio, "visualization.mp3", "audio/mp3")
