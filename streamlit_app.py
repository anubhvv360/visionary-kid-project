# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import pkg_resources
import PIL

# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kids’ Visionboard Generator",
    layout="centered",
    page_icon="📖",
    initial_sidebar_state="collapsed"
)
st.title("📖 Kids’ Visionboard Generator")

# ─── SESSION STATE INITIALIZATION ────────────────────────────────────────────────
if "story_pages" not in st.session_state:
    st.session_state.story_pages = None
if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None
if "saved_name" not in st.session_state:
    st.session_state.saved_name = ""
if "saved_theme" not in st.session_state:
    st.session_state.saved_theme = ""

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "1️⃣ Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="Images uploaded are not saved — the AI model only extracts features for this session."
)
name = st.text_input("2️⃣ What’s your kid’s name?", placeholder="e.g. Bunny")

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

# ─── RESET STATE ON NEW UPLOAD ───────────────────────────────────────────────────
if uploaded_file is not None:
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    if file_id != st.session_state.uploaded_file_id:
        st.session_state.uploaded_file_id = file_id
        st.session_state.story_pages = None
        st.session_state.saved_name = ""
        st.session_state.saved_theme = ""

# ─── SCENARIO GENERATOR ──────────────────────────────────────────────────────────
def generate_scenarios(theme: str, name: str, count: int = 8) -> list[str]:
    if theme == "Different Professions":
        example = f'Format each as "{name} the [profession]" (no location).'
    elif theme == "Value-Based Adventures":
        example = f'Format each as "{name} [action]" (no profession or location).'
    elif theme == "Cultural Landmarks":
        example = f'Format each as "{name} at the [famous landmark]" (no profession).'
    else:
        example = f'Write one-phrase scenarios that fit the theme "{theme}".'

    realism = "Ensure all scenarios are logically consistent (e.g., underwater adventures must include scuba gear)."
    prompt = (
        f"Please list {count} concise, one-phrase story scenarios for a child named {name} "
        f"under the theme \"{theme}\". {example} {realism}\n"
        "Separate each scenario on its own line."
    )

    resp = genai_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["TEXT"])
    )
    text = "".join(part.text or "" for part in resp.candidates[0].content.parts)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return [ln.lstrip("0123456789. -") for ln in lines]

# ─── IMAGE-GENERATION ────────────────────────────────────────────────────────────
def generate_story_pages(image_bytes: bytes, prompts: list[str]):
    pages = []
    img_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    for desc in prompts:
        text_prompt = (
            "Using the uploaded photo as reference, create a single-page, full-color "
            "Pixar-style 3D cartoon illustration in 1024x1024 resolution. "
            "- Keep the same face shape, hair style, eye color, skin tone, and key features "
            "so it unmistakably resembles the child."
            "- Use soft gradients, warm lighting, and stylized proportions typical of Pixar. "
            "- Ensure high quality, detailed rendering suitable for printing. "
            f"Depict the child {desc}. Return only the image (no text)."
        )

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                temperature=0.7,
                max_output_tokens=8192
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break

    return pages

# ─── MAIN LOGIC ─────────────────────────────────────────────────────────────────
if uploaded_file and name and (theme_choice in builtin or custom_theme):
    theme = custom_theme if theme_choice == "Custom" else theme_choice

    if st.button("🖼️ Generate Story Pages"):
        with st.spinner("⏳ Generating scenarios…"):
            prompts = generate_scenarios(theme, name)
        with st.spinner("⏳ Generating scenarios and rendering illustrations…"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        # Persist to session state
        st.session_state.story_pages = story_pages
        st.session_state.saved_name = name
        st.session_state.saved_theme = theme

        st.balloons()

# ─── DISPLAY & DOWNLOAD ─────────────────────────────────────────────────────────
pages = st.session_state.story_pages
if pages:
    for i, (caption, img) in enumerate(pages, start=1):
        st.subheader(f"{caption}")
        st.image(img, use_container_width=True)

        # prepare PNG bytes
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.download_button(
            label=f"⬇️ Download",
            data=buf.getvalue(),
            file_name=f"{st.session_state.saved_name}_page_{i}.png",
            mime="image/png",
            key=f"download_{i}"
        )
else:
    st.info("Please complete steps 1–3 above (and enter a custom theme if you chose ‘Custom’).")

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

st.sidebar.title("ℹ️ About This App")
st.sidebar.markdown("""
    **Kids’ Visionboard Generator** turns a single photo and name into a playful, Pixar-style storyboard.  
    Upload your child’s photo, pick (or type) a theme, and watch custom illustrations come to life—then download each one instantly!
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📦 Library Versions")
st.sidebar.markdown(f"🔹 **Streamlit**: {st.__version__}")
st.sidebar.markdown(f"🔹 **google-genai**: {pkg_resources.get_distribution('google-genai').version}")
st.sidebar.markdown(f"🔹 **Pillow**: {PIL.__version__}")

st.sidebar.markdown("---")
st.sidebar.title("💡 Tips for Best Results")
st.sidebar.markdown("""
- Upload a clear, front-facing photo  
- Use a simple, short name (e.g. “Lily”)  
- Choose a theme or get creative with your own  
- Wait for all illustrations to finish rendering before downloading  
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
Have feedback or ideas? [Reach out!](mailto:anubhav.verma360@gmail.com) 😊
""", unsafe_allow_html=True)

st.sidebar.caption("Disclaimer: This app is for entertainment and creative inspiration. Images are AI-generated and may not be 100% accurate.")


# ─── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    @keyframes gradientAnimation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .animated-gradient {
        background: linear-gradient(90deg, blue, purple, blue);
        background-size: 300% 300%;
        animation: gradientAnimation 8s ease infinite;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
        color: white;
        font-weight: normal;
        font-size: 18px;
    }
    </style>

    <div class="animated-gradient">
        Made with ❤️ by Anubhav Verma
    </div>
""", unsafe_allow_html=True)
