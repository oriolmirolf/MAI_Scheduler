# app.py
import streamlit as st
import json
import matplotlib.pyplot as plt
from itertools import combinations
from matplotlib.colors import ListedColormap

from db import init_db, get_db_session
from auth import register_user, authenticate_user, save_schedule_for_user
from sqlalchemy.orm import Session

from st_pages import Page, show_pages, add_page_title


###############################################################################
# 1) Database initialization
###############################################################################
def init_database():
    init_db()  # Creates tables if needed

###############################################################################
# 2) Schedule-generation logic
###############################################################################
def parse_schedule(schedule_dict):
    schedule_list = []
    for class_type, times in schedule_dict.items():
        for time_str in times:
            day, hours = time_str.split()
            start_hour, end_hour = map(int, hours.split('-'))
            schedule_list.append({
                'day': day,
                'start': start_hour,
                'end': end_hour,
                'class_type': class_type
            })
    return schedule_list

def has_time_conflict(schedule1, schedule2):
    for slot1 in schedule1:
        for slot2 in schedule2:
            if slot1['day'] == slot2['day']:
                if max(slot1['start'], slot2['start']) < min(slot1['end'], slot2['end']):
                    return True
    return False

def combination_has_no_conflicts(course_combination):
    schedules = [course['parsed_schedule'] for code, course in course_combination]
    for i in range(len(schedules)):
        for j in range(i+1, len(schedules)):
            if has_time_conflict(schedules[i], schedules[j]):
                return False
    return True

def combination_respects_university_day_rule(course_combination):
    day_unis = {}
    for code, course in course_combination:
        uni = course['University']
        for slot in course['parsed_schedule']:
            d = slot['day']
            day_unis.setdefault(d, set()).add(uni)
    for d, unis in day_unis.items():
        if len(unis) > 1:
            return False
    return True

def max_consecutive_hours(course_combination, enforce_limit=True):
    max_consec = 0
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for day in days:
        daily_slots = []
        for code, course in course_combination:
            for slot in course['parsed_schedule']:
                if slot['day'] == day:
                    daily_slots.append(slot)
        if not daily_slots:
            continue
        daily_slots.sort(key=lambda x: x['start'])
        merged = []
        current = daily_slots[0].copy()
        for s in daily_slots[1:]:
            if s['start'] <= current['end']:
                current['end'] = max(current['end'], s['end'])
            else:
                merged.append(current)
                current = s.copy()
        merged.append(current)
        day_max = max(s['end'] - s['start'] for s in merged)
        if enforce_limit and day_max > 6:
            return None
        max_consec = max(max_consec, day_max)
    return max_consec

def get_number_of_class_days(course_combination):
    days = set()
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            days.add(slot['day'])
    return len(days)

def total_gap_time(course_combination):
    day_map = {}
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            d = slot['day']
            day_map.setdefault(d, []).append(slot)
    total_gaps = 0
    for d_slots in day_map.values():
        d_slots.sort(key=lambda x: x['start'])
        day_start = d_slots[0]['start']
        day_end = d_slots[-1]['end']
        span = day_end - day_start
        class_time = sum(s['end'] - s['start'] for s in d_slots)
        total_gaps += (span - class_time)
    return total_gaps

def earliest_start_time(course_combination):
    return min(slot['start']
               for code, course in course_combination 
               for slot in course['parsed_schedule'])

def latest_end_time(course_combination):
    return max(slot['end']
               for code, course in course_combination
               for slot in course['parsed_schedule'])

def total_class_hours(course_combination):
    return sum(slot['end'] - slot['start']
               for code, course in course_combination
               for slot in course['parsed_schedule'])

def total_credits(course_combination):
    return sum(course['ECTS'] for code, course in course_combination)

def generate_valid_schedules(courses, min_credits, max_credits, max_days,
                             mandatory_courses, excluded_courses,
                             no_conflicts, uni_day_rule, max_6_consecutive):
    valid = []
    items = [(code, c) for code, c in courses.items() if code not in excluded_courses]
    mandatory_set = set(mandatory_courses)
    from itertools import combinations
    N = len(items)
    for r in range(len(mandatory_courses), N+1):
        for combo in combinations(items, r):
            combo_codes = set(code for code, _ in combo)
            if not mandatory_set.issubset(combo_codes):
                continue
            ects = sum(c['ECTS'] for _, c in combo)
            if not (min_credits <= ects <= max_credits):
                continue
            if no_conflicts and not combination_has_no_conflicts(combo):
                continue
            if uni_day_rule and not combination_respects_university_day_rule(combo):
                continue
            if max_6_consecutive:
                mc = max_consecutive_hours(combo, True)
                if mc is None:
                    continue
            else:
                mc = max_consecutive_hours(combo, False)
            
            days = get_number_of_class_days(combo)
            if days <= max_days:
                valid.append({
                    "combo": combo,
                    "num_days": days,
                    "gap_time": total_gap_time(combo),
                    "max_consec": mc,
                    "total_hours": total_class_hours(combo),
                    "total_ects": total_credits(combo),
                    "earliest_start": earliest_start_time(combo),
                    "latest_end": latest_end_time(combo),
                })
    return valid

def plot_schedule(course_combination):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = ListedColormap(plt.colormaps.get_cmap('tab10').colors[:len(course_combination)])
    course_colors = {}
    
    for i, (code, course) in enumerate(course_combination):
        course_colors[code] = cmap(i)
    
    for code, course in course_combination:
        color = course_colors[code]
        for slot in course['parsed_schedule']:
            d_idx = days.index(slot['day'])
            # Draw bar
            ax.barh(y=slot['start'] + (slot['end'] - slot['start'])/2,
                    width=0.8,
                    height=slot['end'] - slot['start'],
                    left=d_idx - 0.4,
                    color=color,
                    edgecolor='black',
                    align='center')
            ax.text(d_idx,
                    slot['start'] + (slot['end'] - slot['start'])/2,
                    f"{code}\n{slot['class_type']}",
                    ha='center', va='center', color='white', fontsize=8)

    ax.set_ylim(20, 8)
    ax.set_xlim(-0.5, 4.5)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(8,21))
    ax.set_yticklabels([f"{h}:00" for h in range(8,21)])
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Time')
    ax.set_title('Class Schedule')
    plt.tight_layout()
    return fig


###############################################################################
# 3) Streamlit App: Main Page
###############################################################################
def main():
    # st.set_page_config(page_title="Class Schedule Generator", layout="wide", page_icon="📚")
    
    init_database()  # Make sure DB is set up

    st.title("Class Schedule Generator")

    # Session state for user data
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None

    # Make sure we have a flag controlling whether the Login/Register expander is open
    if "show_login_expander" not in st.session_state:
        st.session_state["show_login_expander"] = True

    # -----------------------------
    # OPTIONAL Login / Register
    # -----------------------------
    if st.session_state["show_login_expander"]:
        with st.expander("Login / Register (Optional)", expanded=True):
            colA, colB = st.columns(2)

            with colA:
                st.subheader("Login")
                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login", key="login_button"):
                    db = next(get_db_session())
                    success, user_or_msg = authenticate_user(db, login_username, login_password)
                    db.close()
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user_or_msg.id
                        st.session_state["username"] = user_or_msg.username
                        st.success("Logged in successfully!")
                        # Automatically close the expander
                        st.session_state["show_login_expander"] = False
                        st.experimental_rerun()
                    else:
                        st.error(user_or_msg)

            with colB:
                st.subheader("Register")
                reg_username = st.text_input("New Username", key="register_username")
                reg_password = st.text_input("New Password", type="password", key="register_password")
                if st.button("Register", key="register_button"):
                    db = next(get_db_session())
                    ok, msg = register_user(db, reg_username, reg_password)
                    if ok:
                        # Auto-login right after registration
                        success2, user_or_msg2 = authenticate_user(db, reg_username, reg_password)
                        if success2:
                            st.session_state["logged_in"] = True
                            st.session_state["user_id"] = user_or_msg2.id
                            st.session_state["username"] = user_or_msg2.username
                            st.session_state["show_login_expander"] = False
                            st.success("Registered and logged in!")
                            st.experimental_rerun()
                        else:
                            st.error("Registration was successful, but auto-login failed.")
                    else:
                        st.error(msg)
                    db.close()

        # Logout button outside the expander
        if st.session_state["logged_in"]:
            if st.button("Logout"):
                st.session_state["logged_in"] = False
                st.session_state["user_id"] = None
                st.session_state["username"] = None
                st.experimental_rerun()

    else:
        # Already logged in (or user closed expander)
        if st.session_state["logged_in"]:
            left_col, right_col, space = st.columns([1, 1, 5])
            with left_col:
                st.write(f"Logged in as **{st.session_state['username']}**")
            with right_col:
                if st.button("Logout"):
                    st.session_state["logged_in"] = False
                    st.session_state["user_id"] = None
                    st.session_state["username"] = None
                    st.session_state["show_login_expander"] = True
                    st.experimental_rerun()

    st.write("**Note**: Logging in is optional. If you don't, you can still explore schedules, but not save them.")

    # -----------------------------
    # Load course data
    # -----------------------------
    with open("data.json", "r") as f:
        data = json.load(f)

    # Parse each course schedule
    for code, course in data.items():
        course["parsed_schedule"] = parse_schedule(course["Schedule"])

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("Filters")
    unis = sorted(set(c["University"] for c in data.values()))
    sel_unis = st.sidebar.multiselect("Universities", unis, default=unis)

    max_days = st.sidebar.slider("Max # of class days", 1, 5, 5)
    min_credits, max_credits = st.sidebar.slider("ECTS range",
                                                 0.0, 35.0,
                                                 (30.0, 31.0),
                                                 0.5)

    all_codes = sorted(data.keys())
    mandatory = st.sidebar.multiselect("Mandatory courses", all_codes, default=[])
    excluded = st.sidebar.multiselect("Excluded courses", all_codes, default=[])

    if set(mandatory) & set(excluded):
        st.warning("A course is both mandatory and excluded. Please adjust.")

    st.sidebar.header("Other Options")
    no_conflicts = st.sidebar.checkbox("No Time Conflicts", value=True)
    uni_day_rule = st.sidebar.checkbox("No Different Universities on Same Day", value=True)
    max_6_consecutive = st.sidebar.checkbox("Max 6 Consecutive Hours", value=True)

    # Penalties (for sorting schedules)
    st.sidebar.header("Penalties (affects ordering only)")
    p_days = st.sidebar.slider("Penalty: # days", 0.0, 1.0, 0.2)
    p_gap = st.sidebar.slider("Penalty: Gap time", 0.0, 1.0, 0.2)
    p_consec = st.sidebar.slider("Penalty: Max consecutive", 0.0, 1.0, 0.2)
    p_early = st.sidebar.slider("Penalty: Earliest start", 0.0, 1.0, 0.2)
    p_late = st.sidebar.slider("Penalty: Latest end", 0.0, 1.0, 0.2)

    penalty_list = [p_days, p_gap, p_consec, p_early, p_late]
    total_penalty = sum(penalty_list)
    if total_penalty <= 0:
        st.error("At least one penalty must be > 0.")
        return
    # Normalize
    penalty_list = [p / total_penalty for p in penalty_list]
    p_days, p_gap, p_consec, p_early, p_late = penalty_list

    # -----------------------------
    # Filter data
    # -----------------------------
    filtered_data = {
        code: c for code, c in data.items() if c["University"] in sel_unis
    }

    # -----------------------------
    # Generate valid schedules
    # -----------------------------
    schedules = generate_valid_schedules(
        filtered_data,
        min_credits,
        max_credits,
        max_days,
        mandatory,
        excluded,
        no_conflicts,
        uni_day_rule,
        max_6_consecutive
    )
    if not schedules:
        st.warning("No valid schedules found with these filters.")
        return

    # Prepare normalization for sorting
    d_values = [s["num_days"] for s in schedules]
    g_values = [s["gap_time"] for s in schedules]
    c_values = [s["max_consec"] for s in schedules]
    e_values = [s["earliest_start"] for s in schedules]
    l_values = [s["latest_end"] for s in schedules]

    def normalize(val, minv, maxv, reverse=False):
        if maxv - minv > 0:
            norm = (val - minv)/(maxv - minv)
            return (1 - norm) if reverse else norm
        else:
            return 0

    for s in schedules:
        s["norm_num_days"] = normalize(s["num_days"], min(d_values), max(d_values))
        s["norm_gap_time"] = normalize(s["gap_time"], min(g_values), max(g_values))
        s["norm_max_consec"] = normalize(s["max_consec"], min(c_values), max(c_values))
        s["norm_earliest_start"] = normalize(s["earliest_start"], min(e_values), max(e_values))
        s["norm_latest_end"] = normalize(s["latest_end"], min(l_values), max(l_values))
        s["total_penalty"] = (
            p_days * s["norm_num_days"] +
            p_gap * s["norm_gap_time"] +
            p_consec * s["norm_max_consec"] +
            p_early * s["norm_earliest_start"] +
            p_late * s["norm_latest_end"]
        )

    if "schedule_index" not in st.session_state:
        st.session_state["schedule_index"] = 0
    
    # Sort by penalty ascending
    schedules.sort(key=lambda x: x["total_penalty"])
    idx = st.session_state["schedule_index"]
    selected = schedules[idx]

    st.success(f"Found {len(schedules)} valid schedules.")
    prev_col, next_col, space_col, save_col = st.columns([2, 2, 3, 2])

    with prev_col:
        if st.button("Previous"):
            st.session_state["schedule_index"] = max(
                0, st.session_state["schedule_index"] - 1
            )

    with next_col:
        if st.button("Next"):
            st.session_state["schedule_index"] = min(
                len(schedules) - 1, st.session_state["schedule_index"] + 1
            )

    with save_col:
        if st.session_state["logged_in"]:
            if st.button("Save Schedule"):
                # We'll store just the course codes + some summary
                # so we can reconstruct them on the "SavedCourses" page
                schedule_data = {
                    "course_codes": [c[0] for c in selected["combo"]],
                    "metrics": {
                        "num_days": selected["num_days"],
                        "gap_time": selected["gap_time"],
                        "max_consec": selected["max_consec"],
                        "earliest_start": selected["earliest_start"],
                        "latest_end": selected["latest_end"],
                        "total_penalty": selected["total_penalty"],
                        "total_ects": selected["total_ects"],
                    },
                }
                db = next(get_db_session())
                ok, msg = save_schedule_for_user(
                    db, st.session_state["user_id"], schedule_data
                )
                db.close()
                if ok:
                    st.success("Schedule saved to your account!")
                else:
                    st.error(msg)
        else:
            st.info("Login or register to save schedules.")
            
    st.write(f"Schedule {idx+1} / {len(schedules)}")

    fig = plot_schedule(selected["combo"])
    st.pyplot(fig)
    
    
    st.write(f"**Total ECTS:** {selected['total_ects']}")
    st.write("**Courses in Schedule:**")
    for code, course in selected["combo"]:
        # Add the clickable syllabus link using MBM-{code} pattern
        st.write(
            f"- **{code}** ({course['University']}): {course['ECTS']} ECTS "
            f"- [Syllabus](https://www.fib.upc.edu/en/studies/masters/master-artificial-intelligence/curriculum/syllabus/MAI-{code})"
        )

if __name__ == "__main__":
    
    # add_page_title()
    
    st.set_page_config(page_title="Class Schedule Generator", layout="wide", page_icon="🏠")
    show_pages(
        [
            Page("streamlit_app.py", "Home", "🏠"),
            Page("pages/saved_schedules.py", "Saved Schedules", "💾"),
        ]
    )
    
    main()
