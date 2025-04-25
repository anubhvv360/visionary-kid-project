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
# Read your key from Streamlit secrets
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="We'll use this as the face reference for all drawings."
)

name = st.text_input("What’s your kid’s name?", placeholder="e.g. Robert")

THEMES = {
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

theme_choice = st.selectbox("Choose a story theme", [""] + list(THEMES.keys()))


# ─── GENERATION FUNCTION ────────────────────────────────────────────────────────
def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    # Turn the uploaded bytes into a Part so Gemini can see the face
    img_part = types.Part.from_bytes(image_bytes, mime_type="image/png")

    for desc in prompts:
        text_prompt = (
            "Create a single‐page, full‐color, cartoon‐style illustration of the uploaded child "
            f"doing: {desc}. Return only the image."
        )

        # Pass both the text and image reference
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )

        # Extract the generated image bytes
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break

    return pages


# ─── MAIN APP LOGIC ─────────────────────────────────────────────────────────────
if uploaded_file and name and theme_choice:
    st.success(f"Ready to create your “{theme_choice}” story for {name}!")
    if st.button("Generate Story Pages"):
        with st.spinner("Generating images… this may take a minute"):
            raw_bytes = uploaded_file.read()
            prompts = THEMES[theme_choice]
            story_pages = generate_story_pages(raw_bytes, prompts)

        st.balloons()
        for i, (caption, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {i}: {caption}")
            st.image(img, use_column_width=True)
else:
    st.info("Upload a photo, enter your kid’s name and pick a theme to get started.")
