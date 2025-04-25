# app.py

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


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

# ─── MAIN LOGIC ─────────────────────────────────────────────────────────────────
if uploaded_file and name and (theme_choice in builtin or custom_theme):
    theme = custom_theme if theme_choice == "Custom" else theme_choice

    if st.button("🖼️ Generate Story Pages"):
        with st.spinner("⏳ Generating scenarios…"):
            prompts = generate_scenarios(theme, name)

        with st.spinner("🖌️ Rendering illustrations…"):
            raw = uploaded_file.read()
            story_pages = generate_story_pages(raw, prompts)

        st.balloons()
        for i, (caption, img) in enumerate(story_pages, start=1):
            st.subheader(f"Page {i}: {caption}")
            st.image(img, use_container_width=True)
else:
    st.info("Please complete steps 1–3 above (and enter a custom theme if you chose ‘Custom’).")

def create_storybook_pdf(name: str, theme: str, story_pages: list[tuple[str, Image.Image]]):
    """
    Returns a BytesIO buffer containing a ready-to-print PDF
    with a cover, story pages, and back cover.
    """
    # Map themes to soft background colors
    theme_colors = {
        "Different Professions": colors.lightgrey,
        "Value-Based Adventures": colors.lightgreen,
        "Cultural Landmarks": colors.lightgoldenrodyellow,
    }
    bg = theme_colors.get(theme, colors.lightpink)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    margin = 40

    # ─── Cover Page ────────────────────────────────────────────────────────────────
    c.setFillColor(bg)
    c.rect(0, 0, w, h, stroke=0, fill=1)

    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(colors.white)
    c.drawCentredString(w/2, h*0.65, f"{name}’s {theme} Storybook")

    # Optionally, show a thumbnail of the first illustration
    if story_pages:
        _, first_img = story_pages[0]
        thumb_buf = BytesIO()
        first_img.save(thumb_buf, format="PNG")
        thumb_buf.seek(0)
        reader = ImageReader(thumb_buf)
        # Draw at half width, centered
        tw = w * 0.5
        th = tw
        c.drawImage(reader, (w-tw)/2, h*0.3, tw, th, preserveAspectRatio=True)

    c.showPage()

    # ─── Story Pages ───────────────────────────────────────────────────────────────
    for idx, (caption, img) in enumerate(story_pages, start=1):
        # white background
        c.setFillColor(colors.white)
        c.rect(0, 0, w, h, stroke=0, fill=1)

        # draw the square image centered, leaving room for caption
        img_buf = BytesIO()
        img.convert("RGB").save(img_buf, format="PNG")
        img_buf.seek(0)
        reader = ImageReader(img_buf)

        # compute size: fit into top 80% of page
        max_size = min(w - 2*margin, h*0.8 - margin)
        img_x = (w - max_size) / 2
        img_y = h*0.2
        c.drawImage(reader, img_x, img_y, max_size, max_size, preserveAspectRatio=True)

        # caption area
        c.setFont("Helvetica-Oblique", 14)
        c.setFillColor(colors.darkblue)
        c.drawCentredString(w/2, img_y - 20, caption)

        c.showPage()

    # ─── Back Cover ────────────────────────────────────────────────────────────────
    c.setFillColor(bg)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFont("Helvetica", 16)
    c.setFillColor(colors.white)
    c.drawCentredString(w/2, h/2, "Made with ❤️ by Anubhav Verma")
    c.showPage()

    c.save()
    buf.seek(0)
    return buf

# ─── USAGE ──────────────────────────────────────────────────────────────────────
# after you have `story_pages` and have displayed them:
pdf_buffer = create_storybook_pdf(name, theme, story_pages)
st.download_button(
    label="📖 Download Complete Storybook (PDF)",
    data=pdf_buffer,
    file_name=f"{name}_{theme.replace(' ', '_')}_storybook.pdf",
    mime="application/pdf",
)

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
