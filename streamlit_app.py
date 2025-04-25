# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from langchain.chat_models import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kids’ Storybook Generator",
    layout="centered",
    page_icon="📖"
)
st.title("📖 Kids’ Storybook Generator")

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
# LangChain wrapper for text → scenarios
chat = ChatGoogleGenerativeAI(
    model_name="gemini-2.0-flash",
    api_key=st.secrets["GOOGLE_API_KEY"]
)

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "1️⃣ Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="We'll use this as the face reference for all drawings."
)
name = st.text_input("2️⃣ What’s your kid’s name?", placeholder="e.g. Bunny")

# ─── THEME SELECTION ────────────────────────────────────────────────────────────
builtin = ["Different Professions", "Value-Based Adventures", "Cultural Landmarks"]
theme_choice = st.selectbox(
    "3️⃣ Choose a story theme",
    ["Select…"] + builtin + ["Custom"]
)

custom_theme = ""
if theme_choice == "Custom":
    custom_theme = st.text_input(
        "✏️ Enter your custom theme",
        placeholder="e.g. Underwater Exploration"
    )

# ─── SCENARIO GENERATOR ──────────────────────────────────────────────────────────
def generate_scenarios(theme: str, name: str, count: int = 8) -> list[str]:
    prompt = (
        f"Please list {count} concise, one-phrase story scenarios for a child named {name} "
        f"under the theme “{theme}”. Each scenario should look like “{name} as the pilot in a biplane”."
    )
    # LangChain call into Gemini text
    resp = chat([HumanMessage(content=prompt)])
    # split & clean
    lines = [l.strip() for l in resp.content.splitlines() if l.strip()]
    # remove numbers/bullets
    return [l.lstrip("0123456789. -") for l in lines]

# ─── IMAGE-GENERATION ────────────────────────────────────────────────────────────
def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    img_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    for desc in prompts:
        # Pixar-style + face matching
        text_prompt = (
            "Using the uploaded photo as reference, create a single-page, "
            "full-color Pixar-style 3D cartoon illustration. "
            "- Keep the same face shape, hair style, eye color, skin tone, and key features "
            "so it unmistakably resembles the child. "
            "- Use soft gradients, warm lighting, and stylized proportions typical of Pixar. "
            f"Depict the child {desc}. Return only the image. All images in the same aspect ratio."
        )
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"])
        )
        # extract the first inline image
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break
    return pages

# ─── MAIN ───────────────────────────────────────────────────────────────────────
if uploaded_file and name and (theme_choice in builtin or custom_theme):
    actual_theme = custom_theme if theme_choice == "Custom" else theme_choice

    if st.button("🖼️ Generate Story Pages"):
        with st.spinner("Generating scenarios…"):
            prompts = generate_scenarios(actual_theme, name)
        with st.spinner("Rendering illustrations… this may take a moment"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        st.balloons()
        for i, (cap, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {i}: {cap}")
            st.image(img, use_container_width=True)
else:
    st.info("Complete steps 1️⃣–3️⃣ above (and enter a custom theme if you chose ‘Custom’).")
