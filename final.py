import os
import re
import docx
from openai import OpenAI
import streamlit as st
import time
from dotenv import load_dotenv
import base64

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set your API key securely (in Streamlit secrets)
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔹 Read Word documents
def read_word_doc(filepath):
    doc = docx.Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# 🔹 Extract *generic* discussion points
def extract_generic_points(text, max_points=4):
    prompt = f"""
    You are analyzing multiple team discussion notes. 
    Summarize the following into {max_points} high-level, generic discussion points or lesser if there are not enough points. 
    - Only answer based on the provided text.
    - Avoid specific solutions, names, or numbers. 
    - Keep points broad and neutral to spark further discussion. 
    - Use 3–6 words per point.
    - Do not end with a period.

    Notes:
    {text}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    points = response.choices[0].message.content.split("\n")
    points = [p.strip("-• ") for p in points if p.strip()]
    return points[:max_points]

# 🔹 Process files grouped by Topic_X_Team_Y
def process_all_files(base_folder):
    topics_data = {}

    # Group files by topic number
    topic_files = {}
    for filename in os.listdir(base_folder):
        if filename.endswith(".docx"):
            match = re.match(r"Topic_(\d+)_Team_\d+\.docx", filename)
            if match:
                topic_num = int(match.group(1))
                topic_files.setdefault(topic_num, []).append(filename)

    # Process each topic group
    for topic_num, files in topic_files.items():
        combined_text = ""
        for filename in files:
            filepath = os.path.join(base_folder, filename)
            combined_text += read_word_doc(filepath) + "\n"

        points = extract_generic_points(combined_text)
        topics_data[f"Topic {topic_num}"] = points

    return topics_data


# 🔹 Streamlit display

# Encode image
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Load image
bg_image_path = "background.jpg"
if not os.path.exists(bg_image_path):
    st.error("background.jpg not found!")
    st.stop()

bg_base64 = get_base64_image(bg_image_path)

# --- Custom CSS for layout and style ---
st.set_page_config(layout="wide")
st.markdown(f"""
    <style>
        /* Background Image as fixed div */
        .bg-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            background-image: url('data:image/png;base64,{bg_base64}');
            background-repeat: no-repeat;
            background-size: contain;
            background-position: bottom center;
            opacity: 0.15;
        }}

        /* Make the main app and containers transparent */
        .stApp {{
            background-color: rgba(255, 255, 255, 0.0);
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.0);
            padding: 2rem;
            border-radius: 8px;
        }}
            
        .cross-grid {{
            display: grid;
            grid-template-columns: minmax(400px, 1fr) minmax(400px, 1fr);
            grid-template-rows: auto auto;
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
        }}

        .cross-grid::before,
        .cross-grid::after {{
            content: "";
            position: absolute;
            background-color: #bbb;
        }}

        /* Horizontal center line */
        .cross-grid::before {{
            top: 50%;
            left: 0;
            width: 100%;
            height: 2px;
            transform: translateY(-1px);
        }}

        /* Vertical center line */
        .cross-grid::after {{
            left: 50%;
            top: 0;
            height: 100%;
            width: 2px;
            transform: translateX(-1px);
        }}

        .grid-cell {{
            padding: 40px 60px;
            font-family: Calibri, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            border: 1px solid #cccccc; /* Add border */
            box-sizing: border-box;
        }}

        .grid-cell h3 {{
            text-align: left;
            color: #003366;
            font-size: 35px;
            margin-bottom: 20px;
        }}

        .grid-cell ul {{
            font-size: 25px;
            padding-left: 20px;
            margin: 0;
        }}
        .fade-title {{
            opacity: 0;
            animation: fadeIn 1s forwards;
            animation-delay: 0.1s;
        }}

        @keyframes fadeIn {{
            to {{
                opacity: 1;
            }}
        }}
    </style>
""", unsafe_allow_html=True)

# Insert the background div!
st.markdown('<div class="bg-container"></div>', unsafe_allow_html=True)

def topic_box_animated(title, points, delay=0.4):
    # st.markdown(f"<h3 style='text-align: center; color: #003366;'>{title}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='fade-title'>{title}</h3>", unsafe_allow_html=True)
    container = st.container()
    with container:
        for point in points:
            # Remove any leading numbers like "1.", "2.", etc.
            clean_point = point.lstrip("1234567890. ").strip()
            st.markdown(f"<li style='font-size: 20px; margin-left: 15px;'><b>{clean_point}<b></li>", unsafe_allow_html=True)
            time.sleep(delay)


def main():

    # Load processed data
    base_folder = "team_files"  # folder containing Topic_X_Team_Y.docx
    topics_data = process_all_files(base_folder)

    topics = ["Forecasting & Early Warning", "Disaster Preparedness & Resilience", "Response & Coordination", "Recovery & Reconstruction"]

    # Layout 2x2
    col1_row1, col2_row1 = st.columns([2, 2])

    with col1_row1:
        topic_box_animated(topics[0], topics_data.get("Topic 1", []))
    with col2_row1:
        topic_box_animated(topics[1], topics_data.get("Topic 2", []))

    st.markdown("<div style='margin: 50px 0;'></div>", unsafe_allow_html=True)

    col1_row2, col2_row2 = st.columns([2, 2])

    with col1_row2:
        topic_box_animated(topics[2], topics_data.get("Topic 3", []))
    with col2_row2:
        topic_box_animated(topics[3], topics_data.get("Topic 4", []))


# def main():

#     # Load processed data
#     base_folder = "team_files"  # folder containing Topic_X_Team_Y.docx
#     topics_data = process_all_files(base_folder)

#     # Define 6 slots (Topic 6 will be blank)
#     topics = [
#         "Forecasting & Early Warning",
#         "Disaster Preparedness & Resilience",
#         "Response & Coordination",
#         "Recovery & Reconstruction",
#         "Policy & Governance",
#         ""  # 🔹 Empty slot for Topic 6
#     ]
    

#     # --- Row 1 (3 columns) ---
#     col1_row1, col2_row1, col3_row1 = st.columns([1, 1, 1])

#     with col1_row1:
#         topic_box_animated(topics[0], topics_data.get("Topic 1", []))
#     with col2_row1:
#         topic_box_animated(topics[1], topics_data.get("Topic 2", []))
#     with col3_row1:
#         topic_box_animated(topics[2], topics_data.get("Topic 3", []))

#     # 🔹 Add vertical spacing between rows
#     st.markdown("<div style='margin: 50px 0;'></div>", unsafe_allow_html=True)

#     # --- Row 2 (3 columns) ---
#     col1_row2, col2_row2, col3_row2 = st.columns([1, 1, 1])

#     with col1_row2:
#         topic_box_animated(topics[3], topics_data.get("Topic 4", []))
#     with col2_row2:
#         topic_box_animated(topics[4], topics_data.get("Topic 5", []))
#     with col3_row2:
#         st.empty()  # keeps layout aligned but blank

if __name__ == "__main__":
    main()
