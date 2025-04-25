# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import textwrap


# ─── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kids’ Storybook Generator",
    layout="centered",
    page_icon="📖"
)
st.title("📖 Kids’ Storybook Generator")

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# ─── USER INPUT ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "1️⃣ Upload a photo of your kid",
    type=["png", "jpg", "jpeg"],
    help="Images uploaded are not saved — the AI model only extracts features for this session."
)

#st.caption("Images uploaded are not saved — the AI model only extracts features for this session.")

name = st.text_input("2️⃣ What’s your kid’s name?", placeholder="e.g. Robert")

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
    # Decide example formatting rules per theme
    if theme == "Different Professions":
        example = f'Format each as "{name} the [profession]" (no location).'
    elif theme == "Value-Based Adventures":
        example = f'Format each as "{name} [action]" (no profession or location).'
    elif theme == "Cultural Landmarks":
        example = f'Format each as "{name} at the [famous landmark]" (no profession).'
    else:
        example = f'Write one-phrase scenarios that fit the theme "{theme}".'

    # Realism check
    realism = "Ensure all scenarios are logically consistent (e.g., underwater adventures must include scuba gear)."

    prompt = (
        f"Please list {count} concise, one-phrase story scenarios for a child named {name} "
        f"under the theme \"{theme}\". {example} {realism}\n"
        "Separate each scenario on its own line."
    )

    # Call Gemini text
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
            "Pixar-style 3D cartoon illustration. "
            "- Keep the same face shape, hair style, eye color, skin tone, and key features "
            "so it unmistakably resembles the child. "
            "- Use soft gradients, warm lighting, and stylized proportions typical of Pixar. "
            "- Use a 1:1 square aspect ratio (e.g. 512×512). "
            f"Depict the child {desc}. Return only the image (no text)."
        )

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[text_prompt, img_part],
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                pages.append((desc, img))
                break

    return pages



# ─── REGISTER Sniglet FONT ────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont("Sniglet", "Sniglet-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sniglet-Bold", "Sniglet-Bold.ttf"))

def create_storybook_pdf(name: str, theme: str, story_pages: list[tuple[str, Image.Image]]):
    # ─── CONFIG ────────────────────────────────────────────────────────────────────
    # square size in points (600pt ≈ 8.3")
    size = 600
    bg_colors = {
        "Different Professions": colors.HexColor("#FF7F50"),       # coral
        "Value-Based Adventures": colors.HexColor("#32CD32"),      # lime green
        "Cultural Landmarks": colors.HexColor("#1E90FF"),          # dodger blue
    }
    cover_bg = bg_colors.get(theme, colors.HexColor("#FF6F91"))    # fallback pink

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(size, size))
    w, h = size, size
    margin = 30

    # ─── COVER ─────────────────────────────────────────────────────────────────────
    c.setFillColor(cover_bg)
    c.rect(0, 0, w, h, stroke=0, fill=1)

    title = f"{name}’s {theme} Storybook"
    lines = textwrap.wrap(title, width=18)
    y_start = h * 0.75
    c.setFont("Sniglet-Bold", 48)
    c.setFillColor(colors.white)
    for i, line in enumerate(lines):
        c.drawCentredString(w/2, y_start - i*60, line)

    # thumbnail of first page
    if story_pages:
        _, first_img = story_pages[0]
        thumb = BytesIO()
        first_img.save(thumb, "PNG")
        thumb.seek(0)
        reader = ImageReader(thumb)
        tw = w * 0.5
        c.drawImage(reader, (w-tw)/2, h*0.35, tw, tw, preserveAspectRatio=True)

    c.showPage()

    # ─── CONTENT PAGES ────────────────────────────────────────────────────────────
    for idx, (caption, img) in enumerate(story_pages, start=1):
        # vibrant background
        c.setFillColor(colors.whitesmoke)
        c.rect(0, 0, w, h, stroke=0, fill=1)

        # draw the square image (80% of page width)
        img_buf = BytesIO()
        img.convert("RGB").save(img_buf, "PNG")
        img_buf.seek(0)
        reader = ImageReader(img_buf)
        img_size = w * 0.8
        x = (w - img_size)/2
        y = (h - img_size)/2 + 30  # leave room below
        c.drawImage(reader, x, y, img_size, img_size, preserveAspectRatio=True)

        # caption below image
        c.setFont("Sniglet", 18)
        c.setFillColor(colors.darkblue)
        c.drawCentredString(w/2, y - 25, caption)

        c.showPage()

    # ─── BACK COVER ───────────────────────────────────────────────────────────────
    back_bg = colors.HexColor("#2F4F4F")  # dark slate gray
    c.setFillColor(back_bg)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFont("Sniglet-Bold", 24)
    c.setFillColor(colors.whitesmoke)
    c.drawCentredString(w/2, h/2, "Made with ❤️ by Anubhav Verma")
    c.showPage()

    c.save()
    buf.seek(0)
    return buf


# ─── MAIN LOGIC ─────────────────────────────────────────────────────────────────
if uploaded_file and name and (theme_choice in builtin or custom_theme):
    theme = custom_theme if theme_choice == "Custom" else theme_choice

    if st.button("🖼️ Generate Story Pages"):
        # 1️⃣ Generate scenarios & images
        with st.spinner("⏳ Generating scenarios…"):
            prompts = generate_scenarios(theme, name)
        with st.spinner("🖌️ Rendering illustrations…"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        st.balloons()
        # 2️⃣ Display each page

     
        for i, (caption, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {i}: {caption}")
            st.image(img, use_container_width=True)
#else:
#    st.info("Please complete steps 1–3 above (and enter a custom theme if you chose ‘Custom’).")

# ─── USAGE ──────────────────────────────────────────────────────────────────────
# after you have `story_pages` and have displayed them:
        pdf_buffer = create_storybook_pdf(name, theme, story_pages)
        st.download_button(
            label="📖 Download Complete Storybook (PDF)",
            data=pdf_buffer,
            file_name=f"{name}_{theme.replace(' ', '_')}_storybook.pdf",
            mime="application/pdf",
        )
else:
    st.info("Please complete steps 1–3 above (and enter a custom theme if you chose ‘Custom’).")

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
