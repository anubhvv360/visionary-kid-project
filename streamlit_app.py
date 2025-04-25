# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Kids’ Storybook Generator", layout="centered", page_icon="📖")
st.title("📖 Kids’ Storybook Generator")

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
# Make sure your .streamlit/secrets.toml contains:
# GOOGLE_API_KEY = "your_api_key_here"
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="We'll use this as the face reference for all drawings."
)

name = st.text_input("What’s your kid’s name?", placeholder="e.g. Robert")

# ─── THEME SELECTION ────────────────────────────────────────────────────────────
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

theme_choice = st.selectbox(
    "Choose a story theme",
    ["", *DEFAULT_THEMES.keys(), "Custom"]
)

# If custom, ask for comma-separated prompts
if theme_choice == "Custom":
    prompts_raw = st.text_area(
        "Enter your own prompts (comma separated)",
        placeholder=(
            "e.g. Robert as an astronaut, Robert exploring Mars, "
            "Robert baking a cake"
        ),
        height=100
    )
    prompts = [p.strip() for p in prompts_raw.split(",") if p.strip()]
elif theme_choice in DEFAULT_THEMES:
    prompts = DEFAULT_THEMES[theme_choice]
else:
    prompts = []

# ─── IMAGE-GEN FUNCTION ─────────────────────────────────────────────────────────
def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    # wrap the raw bytes so Gemini sees your kid’s face
    img_part = types.Part.from_bytes(image_bytes, mime_type="image/png")

    for desc in prompts:
        text_prompt = (
            "Create a single-page, full-color, cartoon-style illustration "
            f"of the uploaded child doing: {desc}. Return only the image."
        )

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )

        # pull out the first returned image
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break

    return pages

# ─── MAIN APP LOGIC ─────────────────────────────────────────────────────────────
if uploaded_file and name and prompts:
    st.success(f"Ready to create your “{theme_choice}” story for {name}!")
    if st.button("Generate Story Pages"):
        with st.spinner("Generating images… this may take a minute"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        st.balloons()
        for i, (caption, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {i}: {caption}")
            st.image(img, use_column_width=True)

else:
    st.info("Upload a photo, enter a name, pick (or type) a theme, then generate.")

