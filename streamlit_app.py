# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kids’ Storybook Generator",
    layout="centered",
    page_icon="📖"
)
st.title("📖 Kids’ Storybook Generator")

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
# Make sure .streamlit/secrets.toml contains:
# GOOGLE_API_KEY = "your_api_key_here"
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "1️⃣ Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="We'll use this as the face reference for all drawings."
)
name = st.text_input("2️⃣ What’s your kid’s name?", placeholder="e.g. Robert")

# ─── DEFINE BUILT-IN THEMES ─────────────────────────────────────────────────────
DEFAULT_THEMES = {
    "Different Professions": [
        f"{name} the doctor",
        f"{name} the pilot",
        f"{name} the firefighter",
        f"{name} the scientist",
    ],
    "Value-Based Adventures": [
        f"{name} cleaning their play area",
        f"{name} helping an elder cross the street",
        f"{name} sharing toys with a friend",
    ],
    "Cultural Landmarks": [
        f"{name} at the Pyramids of Egypt",
        f"{name} at the Taj Mahal, India",
        f"{name} at the Eiffel Tower, France",
    ],
}

# ─── THEME SELECTION ────────────────────────────────────────────────────────────
theme_options = [
    "Select a theme…",
    *DEFAULT_THEMES.keys(),
    "Custom"
]
theme_choice = st.selectbox("3️⃣ Choose a story theme", theme_options)

# ─── CUSTOM PROMPTS ─────────────────────────────────────────────────────────────
if theme_choice == "Custom":
    prompts_raw = st.text_area(
        "🔤 Enter your own prompts (comma separated)",
        placeholder=(
            "e.g. Robert as an astronaut, "
            "Robert exploring Mars, "
            "Robert baking a cake"
        ),
        height=100,
    )
    prompts = [p.strip() for p in prompts_raw.split(",") if p.strip()]
elif theme_choice in DEFAULT_THEMES:
    prompts = DEFAULT_THEMES[theme_choice]
else:
    prompts = []

# ─── IMAGE-GENERATION ────────────────────────────────────────────────────────────
def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    # wrap bytes so Gemini sees the face
    img_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    for desc in prompts:
        text_prompt = (
            "Create a single-page, full-color, pixar style illustration (keeping exact same face as reference) of "
            f"the uploaded child doing: {desc}. Return only the image."
        )

        # request both TEXT and IMAGE modalities
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        # discard any text and pull out the first inline image
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break

    return pages

# ─── RENDER ─────────────────────────────────────────────────────────────────────
if uploaded_file and name and prompts:
    if st.button("🖼️ Generate Story Pages"):
        with st.spinner("Generating images… this may take a minute"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        st.balloons()
        for idx, (caption, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {idx}: {caption}")
            st.image(img, use_column_width=True)
else:
    st.info("Please complete steps 1️⃣–3️⃣ above before generating.")
