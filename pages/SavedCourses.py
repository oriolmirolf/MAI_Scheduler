# pages/SavedCourses.py
import streamlit as st
import json
from db import get_db_session
from auth import get_user_schedules
from streamlit_app import parse_schedule, plot_schedule

def load_course_data():
    """Helper to load data.json. Adjust path if needed."""
    with open("data.json", "r") as f:
        data = json.load(f)
    # parse the schedules
    for code, course in data.items():
        course["parsed_schedule"] = parse_schedule(course["Schedule"])
    return data

def main():
    st.set_page_config(page_title="Saved Schedules", layout="wide")
    st.title("Your Saved Schedules")

    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("You must be logged in to view your saved schedules.")
        return

    # If logged in, load from DB
    db = next(get_db_session())
    schedules = get_user_schedules(db, st.session_state["user_id"])
    db.close()

    if not schedules:
        st.info("You have no saved schedules yet.")
        return

    # Let user select which saved schedule to view
    choice = st.selectbox("Pick a schedule to view", range(len(schedules)), format_func=lambda i: f"Schedule #{i+1}")
    chosen = schedules[choice]
    st.write(f"**Viewing Schedule #{choice+1}**")

    # Reconstruct the schedule from 'course_codes' using data.json
    data = load_course_data()
    codes = chosen["course_codes"]
    # Build a "combo"
    combo = []
    for c in codes:
        if c in data:
            combo.append((c, data[c]))
        else:
            st.warning(f"Course code {c} not found in data.json. Skipping.")
    
    # Plot the schedule
    if combo:
        fig = plot_schedule(combo)
        st.pyplot(fig)

        # Show some stored metrics
        metrics = chosen.get("metrics", {})
        st.write("**Metrics:**")
        st.json(metrics)
    else:
        st.warning("No valid courses to display.")

if __name__ == "__main__":
    main()
