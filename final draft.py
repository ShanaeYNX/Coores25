import os
import re
import docx
from openai import OpenAI
import streamlit as st
import time
import html
import random
import string
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set your API key securely (in Streamlit secrets)
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔹 Read Word documents
def read_word_doc(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

# 🔹 Extract *generic* discussion points
def extract_generic_points(text, max_points=5):
    prompt = f"""
    You are analyzing multiple team discussion notes. 
    Summarize the following into maximum {max_points} high-level, generic discussion points. 
    - Only use the information provided under Notes.
    - Avoid specific solutions, names, or numbers. 
    - Keep points broad and neutral to spark further discussion. 
    - Use 3–6 words per point.
    - Do not end with a period

    Notes:
    {text}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    points = response.choices[0].message.content.split("\n")
    return [p.strip("-• ") for p in points if p.strip()][:max_points]

# 🔹 Process all Topic_X_Team_Y.docx files
def process_all_files(base_folder):
    topics_data = {}
    topic_files = {}

    for filename in os.listdir(base_folder):
        if filename.endswith(".docx"):
            match = re.match(r"Topic_(\d+)_Team_\d+\.docx", filename)
            if match:
                topic_num = int(match.group(1))
                topic_files.setdefault(topic_num, []).append(filename)

    for topic_num, files in topic_files.items():
        combined_text = ""
        for filename in files:
            filepath = os.path.join(base_folder, filename)
            combined_text += read_word_doc(filepath) + "\n"

        topics_data[f"Topic {topic_num}"] = extract_generic_points(combined_text)

    return topics_data

# 🔹 Streamlit setup
st.set_page_config(layout="wide")

# 🔹 Inject HTML/CSS with animation
st.markdown("""
<style>
.grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 0;
    width: 100%;
    max-width: 1600px;
    margin: 40px auto;
    border-collapse: collapse;
}

/* Basic cell styling */
.grid-cell {
    padding: 40px 60px;
    border: 1px solid #ccc;
    font-family: Calibri, sans-serif;
    background-color: white;
}

/* Remove top border on first row */
.grid-cell:nth-child(1),
.grid-cell:nth-child(2) {
    border-top: none;
}

/* Remove left border on first column */
.grid-cell:nth-child(1),
.grid-cell:nth-child(3) {
    border-left: none;
}

/* Remove right border on second column */
.grid-cell:nth-child(2),
.grid-cell:nth-child(4) {
    border-right: none;
}

/* Remove bottom border on last row */
.grid-cell:nth-child(3),
.grid-cell:nth-child(4) {
    border-bottom: none;
}

/* Heading style */
.grid-cell h3 {
    color: #003366;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 0px;
}

/* List style */
.grid-cell ul {
    font-size: 23px;
    margin: 0;
    padding-left: 20px;
}

/* Fade-in animation for list items */
.grid-cell li {
    opacity: 0;
    animation: fadeInUp 0.6s ease forwards;
    animation-delay: calc(var(--order) * 0.4s);
}

@keyframes fadeInUp {
    0% {
        opacity: 0;
        transform: translateY(10px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
""", unsafe_allow_html=True)



# 🔹 Render a single grid cell with forced animation
def render_cell(title, points):
    html_content = f"<div class='grid-cell'><h3>{title}</h3><ul>"
    unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    for idx, point in enumerate(points):
        safe_point = html.escape(point)
        # Create a unique class name per run per list item to retrigger animation
        unique_class = f"anim-{idx}-{unique_suffix}"
        html_content += f"<li class='{unique_class}' style='--order:{idx}'>{safe_point}</li>"

    html_content += "</ul></div>"
    return html_content

# 🔹 Main layout logic
def main():
    base_folder = "team_files"
    topics_data = process_all_files(base_folder)

    topic_titles = [
        "Forecasting & Early Warning",
        "Disaster Preparedness & Resilience",
        "Response & Coordination",
        "Recovery & Reconstruction"
    ]

    # Generate each cell and inject into 2x2 grid
    grid_html = "<div class='grid-container'>"
    grid_html += render_cell(topic_titles[0], topics_data.get("Topic 1", []))  # Top-left
    grid_html += render_cell(topic_titles[1], topics_data.get("Topic 2", []))  # Top-right
    grid_html += render_cell(topic_titles[2], topics_data.get("Topic 3", []))  # Bottom-left
    grid_html += render_cell(topic_titles[3], topics_data.get("Topic 4", []))  # Bottom-right
    grid_html += "</div>"

    st.markdown(grid_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    