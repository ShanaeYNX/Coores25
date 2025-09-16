import os
import re
import docx
from openai import OpenAI
import streamlit as st
import time
from dotenv import load_dotenv
import re

# 🔹 Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔹 Set up OpenAI client (v1.x)
client = OpenAI(api_key=OPENAI_API_KEY)


# 🔹 Read Word document text
def read_word_doc(filepath):
    doc = docx.Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


# 🔹 Extract discussion points using GPT
def extract_generic_points(text, max_points=7):
    prompt = f"""
    You are analyzing multiple team discussion notes. 
    Summarize the following into {max_points} high-level, generic discussion points or lesser if thee are not enough points. 
    - Only answer based on the provided text.
    - Avoid specific solutions, names, or numbers. 
    - Keep points broad and neutral to spark further discussion. 
    - Use 3–6 words per point.
    - Do not end with a period.

    Notes:
    {text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        points = response.choices[0].message.content.split("\n")
        points = [
            re.sub(r"^\d+[\).]?\s*", "", p.strip("-• ").strip())
            for p in points if p.strip()
        ]
        return points[:max_points]
    except Exception as e:
        return [f"Error: {str(e)}"]


# 🔹 Process all Topic_X_Team_Y files
@st.cache_data
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

        points = extract_generic_points(combined_text)
        topics_data[f"Topic {topic_num}"] = points

    return topics_data


# 🔹 Custom styling
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .fade-title {
            opacity: 0;
            animation: fadeIn 1s forwards;
            animation-delay: 0.1s;
        }

        @keyframes fadeIn {
            to {
                opacity: 1;
            }
        }
    </style>
""", unsafe_allow_html=True)


# 🔹 Display topic content with animation
def topic_box_animated(title, points, delay=0.4):
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='fade-title'>{title}</h3>", unsafe_allow_html=True)
    container = st.container()
    with container:
        for point in points:
            clean_point = re.sub(r"^\d+[\).]?\s*", "", point).strip()
            st.markdown(f"<li style='font-size: 20px; margin-left: 15px;'>{clean_point}</li>", unsafe_allow_html=True)
            time.sleep(delay)


# 🔹 Main app logic
def main():
    base_folder = "team_files"  # Folder containing Topic_X_Team_Y.docx files
    topics_data = process_all_files(base_folder)

    # Tab titles (edit as needed)
    tabs = st.tabs([
        "Forecasting & Early Warning",
        "Disaster Preparedness & Resilience",
        "Response & Coordination",
        "Recovery & Reconstruction"
    ])

    with tabs[0]:
        topic_box_animated("Forecasting & Early Warning", topics_data.get("Topic 1", []))

    with tabs[1]:
        topic_box_animated("Disaster Preparedness & Resilience", topics_data.get("Topic 2", []))

    with tabs[2]:
        topic_box_animated("Response & Coordination", topics_data.get("Topic 3", []))

    with tabs[3]:
        topic_box_animated("Recovery & Reconstruction", topics_data.get("Topic 4", []))


# 🔹 Run the app
if __name__ == "__main__":
    main()
