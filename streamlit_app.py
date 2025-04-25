# app.py
import streamlit as st
import google.generativeai as genai
from google.generativeai import types
from PIL import Image
from io import BytesIO

# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Kids’ Storybook Generator", layout="centered", page_icon="📖")
st.title("📖 Kids’ Storybook Generator")

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
genai.api_key = st.secrets["GOOGLE_API_KEY"]

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload a photo of your kid", type=["png","jpg","jpeg"])
name = st.text_input("What’s your kid’s name?", placeholder="e.g. Robert")

THEMES = {
    "Different Professions": [f"{name} the doctor", f"{name} the pilot", ...],
}

theme_choice = st.selectbox("Choose a story theme", [""] + list(THEMES.keys()))

def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    for desc in prompts:
        prompt = (f"Create a single-page, cartoon illustration of the uploaded child doing: {desc}. "
                  "Return only the image.")
        response = genai.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )
        # pull out the inline image bytes
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break
    return pages

if uploaded_file and name and theme_choice:
    if st.button("Generate Story Pages"):
        with st.spinner("Generating…"):
            pages = generate_story_pages(uploaded_file.read(), THEMES[theme_choice])
        for i,(cap,img) in enumerate(pages,1):
            st.subheader(f"Page {i}: {cap}")
            st.image(img, use_column_width=True)
else:
    st.info("Please upload a photo, enter name & pick a theme.")
