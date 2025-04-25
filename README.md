# 📖 Kids’ Visionboard Generator

Get a personalised visionboard for your kid!

A fun, interactive Streamlit app that turns a child’s photo and name into a personalised visionboard storybook. Powered by Google’s Gemini multimodal models via the `google-genai` SDK, this tool:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://visionary-kid.streamlit.app/)

- **Inputs** a kid’s photo (PNG/JPG) and name  
- **Dynamically generates** 8 themed “scenario” prompts  
- **Renders** custom Pixar-style, face-matched illustrations  
- **Displays** each page in a square format  
- **Lets parents download** individual pages with one-click buttons  
- **Delivers** playful UI feedback with baloons

---

## 🚀 Features

- **Custom themes**  
  - Built-in: Professions, Value-based adventures, Cultural landmarks  
  - **Custom**: Type any theme (e.g. “Underwater Exploration”)  
- **Realism guardrails** ensure logical consistency (e.g., scuba gear underwater)  
- **Session persistence** so pages stay visible even after downloads  
- **Per-image downloads**—no bulky ZIPs or PDFs required  
- **Interactive toasts** (“So cute, that’s a lovely name!”) when you upload a photo or enter a name  
- **Animated footer** crediting the creator

---

## 📋 Requirements

- Python 3.8+  
- Streamlit > 1.12  
- `google-genai` >= 1.12.1  
- Pillow  

Add to your `requirements.txt`:

```txt
streamlit
google-genai>=1.12.1
Pillow
