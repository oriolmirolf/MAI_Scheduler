import json
import streamlit as st
from itertools import combinations
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

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
                latest_start = max(slot1['start'], slot2['start'])
                earliest_end = min(slot1['end'], slot2['end'])
                if latest_start < earliest_end:
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
    day_universities = {}
    for code, course in course_combination:
        uni = course['University']
        for slot in course['parsed_schedule']:
            day = slot['day']
            if day not in day_universities:
                day_universities[day] = set()
            day_universities[day].add(uni)
    for day, universities in day_universities.items():
        if len(universities) > 1:
            return False
    return True

def no_more_than_6_consecutive_hours(course_combination):
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        slots = []
        for code, course in course_combination:
            for slot in course['parsed_schedule']:
                if slot['day'] == day:
                    slots.append(slot)
        if not slots:
            continue
        slots.sort(key=lambda x: x['start'])
        merged_slots = []
        current_slot = slots[0].copy()
        for slot in slots[1:]:
            if slot['start'] <= current_slot['end']:
                current_slot['end'] = max(current_slot['end'], slot['end'])
            else:
                merged_slots.append(current_slot)
                current_slot = slot.copy()
        merged_slots.append(current_slot)
        for slot in merged_slots:
            if slot['end'] - slot['start'] > 6:
                return False
    return True

def get_number_of_class_days(course_combination):
    days_with_classes = set()
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            days_with_classes.add(slot['day'])
    return len(days_with_classes)

def total_gap_time(course_combination):
    days = {}
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            day = slot['day']
            if day not in days:
                days[day] = []
            days[day].append(slot)
    total_gap = 0
    for slots in days.values():
        slots.sort(key=lambda x: x['start'])
        day_start = slots[0]['start']
        day_end = slots[-1]['end']
        span = day_end - day_start
        class_time = sum(slot['end'] - slot['start'] for slot in slots)
        total_gap += span - class_time
    return total_gap

def max_consecutive_hours(course_combination):
    max_consecutive = 0
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        slots = []
        for code, course in course_combination:
            for slot in course['parsed_schedule']:
                if slot['day'] == day:
                    slots.append(slot)
        if not slots:
            continue
        slots.sort(key=lambda x: x['start'])
        merged_slots = []
        current_slot = slots[0].copy()
        for slot in slots[1:]:
            if slot['start'] <= current_slot['end']:
                current_slot['end'] = max(current_slot['end'], slot['end'])
            else:
                merged_slots.append(current_slot)
                current_slot = slot.copy()
        merged_slots.append(current_slot)
        day_max_consecutive = max(slot['end'] - slot['start'] for slot in merged_slots)
        if day_max_consecutive > 6:
            return None  # Exceeds the 6-hour limit
        if day_max_consecutive > max_consecutive:
            max_consecutive = day_max_consecutive
    return max_consecutive

def earliest_start_time(course_combination):
    earliest = 24
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            if slot['start'] < earliest:
                earliest = slot['start']
    return earliest

def latest_end_time(course_combination):
    latest = 0
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            if slot['end'] > latest:
                latest = slot['end']
    return latest

def total_class_hours(course_combination):
    total_hours = 0
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            total_hours += slot['end'] - slot['start']
    return total_hours

def total_credits(course_combination):
    return sum(course['ECTS'] for code, course in course_combination)

def generate_valid_schedules(courses, min_credits, max_credits, max_days, mandatory_courses):
    valid_schedules = []
    course_items = list(courses.items())
    N = len(course_items)
    mandatory_course_codes = set(mandatory_courses)
    for r in range(len(mandatory_courses), N+1):
        for course_combination in combinations(course_items, r):
            course_codes = set(code for code, _ in course_combination)
            if not mandatory_course_codes.issubset(course_codes):
                continue  # Mandatory courses not included
            total_ects = sum(course['ECTS'] for code, course in course_combination)
            if min_credits <= total_ects <= max_credits:
                if combination_has_no_conflicts(course_combination):
                    if combination_respects_university_day_rule(course_combination):
                        if no_more_than_6_consecutive_hours(course_combination):
                            num_class_days = get_number_of_class_days(course_combination)
                            if num_class_days <= max_days:
                                max_consec = max_consecutive_hours(course_combination)
                                if max_consec is not None:
                                    valid_schedules.append({
                                        'combo': course_combination,
                                        'num_days': num_class_days,
                                        'gap_time': total_gap_time(course_combination),
                                        'max_consec': max_consec,
                                        'total_hours': total_class_hours(course_combination),
                                        'total_ects': total_credits(course_combination),
                                        'earliest_start': earliest_start_time(course_combination),
                                        'latest_end': latest_end_time(course_combination),
                                    })
    return valid_schedules

def plot_schedule(course_combination):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    fig, ax = plt.subplots(figsize=(10, 6))

    # Prepare colors
    colors = ListedColormap(plt.colormaps.get_cmap('tab10').colors[:len(course_combination)])
    course_colors = {}
    for idx, (code, course) in enumerate(course_combination):
        course_colors[code] = colors(idx)

    for code, course in course_combination:
        color = course_colors[code]
        for slot in course['parsed_schedule']:
            day_idx = days.index(slot['day'])
            # Draw the rectangle
            ax.barh(
                y=slot['start'] + (slot['end'] - slot['start']) / 2,
                width=0.8,
                height=slot['end'] - slot['start'],
                left=day_idx - 0.4,
                color=color,
                edgecolor='black',
                align='center'
            )
            ax.text(
                day_idx,
                slot['start'] + (slot['end'] - slot['start']) / 2,
                f"{code}\n{slot['class_type']}",
                ha='center', va='center', color='white', fontsize=8
            )

    ax.set_ylim(20, 8)  # Invert y-axis to have time increase from top to bottom
    ax.set_xlim(-0.5, 4.5)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(8, 21))
    ax.set_yticklabels([f"{hour}:00" for hour in range(8, 21)])
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Time')
    ax.set_title('Class Schedule')
    plt.tight_layout()
    return fig

def main():
    st.title("Class Schedule Generator")

    # Load data
    with open('data.json', 'r') as f:
        data = json.load(f)

    # Parse schedules
    for code, course in data.items():
        course['parsed_schedule'] = parse_schedule(course['Schedule'])

    # Sidebar inputs
    st.sidebar.header("Filters")
    universities_list = sorted(set(course['University'] for course in data.values()))
    selected_universities = st.sidebar.multiselect("Select Universities", universities_list, default=universities_list)

    max_days_per_week = st.sidebar.slider(
        "Maximum number of class days per week", 1, 5, 5)

    min_credits, max_credits = st.sidebar.slider(
        "Select ECTS range",
        min_value=0.0,
        max_value=35.0,
        value=(30.0, 30.0),
        step=0.5
    )

    # Mandatory courses
    st.sidebar.header("Mandatory Courses")
    course_codes = sorted(data.keys())
    mandatory_courses = st.sidebar.multiselect("Select mandatory courses", course_codes, default=[])

    # Penalties
    st.sidebar.header("Penalties")
    p_num_days = st.sidebar.slider("Penalty for Number of Class Days", 0.0, 1.0, 0.2)
    p_gap_time = st.sidebar.slider("Penalty for Total Gap Time", 0.0, 1.0, 0.2)
    p_max_consecutive = st.sidebar.slider("Penalty for Max Consecutive Hours", 0.0, 1.0, 0.2)
    p_earliest_start = st.sidebar.slider("Penalty for Starting Early", 0.0, 1.0, 0.2)
    p_latest_end = st.sidebar.slider("Penalty for Ending Late", 0.0, 1.0, 0.2)

    # Normalize penalties to sum to 1
    penalties = [p_num_days, p_gap_time, p_max_consecutive, p_earliest_start, p_latest_end]
    total_penalty_weight = sum(penalties)
    if total_penalty_weight > 0:
        penalties = [p / total_penalty_weight for p in penalties]
    else:
        st.error("At least one penalty must be greater than zero.")
        return

    p_num_days, p_gap_time, p_max_consecutive, p_earliest_start, p_latest_end = penalties

    # Filter courses
    filtered_courses = {
        code: course for code, course in data.items()
        if course['University'] in selected_universities
    }

    # Generate valid schedules
    valid_schedules = generate_valid_schedules(
        filtered_courses, min_credits, max_credits, max_days_per_week, mandatory_courses)

    if not valid_schedules:
        st.warning("No valid schedules found with the given criteria.")
        return

    # Compute min and max for normalization
    num_days_values = [s['num_days'] for s in valid_schedules]
    gap_time_values = [s['gap_time'] for s in valid_schedules]
    max_consec_values = [s['max_consec'] for s in valid_schedules]
    earliest_start_values = [s['earliest_start'] for s in valid_schedules]
    latest_end_values = [s['latest_end'] for s in valid_schedules]

    # Normalization function with reverse option
    def normalize(value, min_value, max_value, reverse=False):
        if max_value - min_value > 0:
            normalized = (value - min_value) / (max_value - min_value)
            if reverse:
                return 1 - normalized
            else:
                return normalized
        else:
            return 0.0

    # Normalize and compute penalty scores
    for s in valid_schedules:
        s['norm_num_days'] = normalize(s['num_days'], min(num_days_values), max(num_days_values), reverse=False)
        s['norm_gap_time'] = normalize(s['gap_time'], min(gap_time_values), max(gap_time_values), reverse=False)
        s['norm_max_consec'] = normalize(s['max_consec'], min(max_consec_values), max(max_consec_values), reverse=False)
        s['norm_earliest_start'] = normalize(s['earliest_start'], min(earliest_start_values), max(earliest_start_values), reverse=False)
        s['norm_latest_end'] = normalize(s['latest_end'], min(latest_end_values), max(latest_end_values), reverse=False)

        # Compute total penalty
        s['total_penalty'] = (
            p_num_days * s['norm_num_days'] +
            p_gap_time * s['norm_gap_time'] +
            p_max_consecutive * s['norm_max_consec'] +
            p_earliest_start * s['norm_earliest_start'] +
            p_latest_end * s['norm_latest_end']
        )

    # Sort schedules by total penalty (lower is better)
    valid_schedules.sort(key=lambda s: s['total_penalty'])

    # Initialize session state for schedule index
    if 'schedule_index' not in st.session_state:
        st.session_state.schedule_index = 0

    # Navigation buttons (placed before plotting)
    st.success(f"Found {len(valid_schedules)} valid schedules.")
    col1, _, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Previous"):
            if st.session_state.schedule_index > 0:
                st.session_state.schedule_index -= 1
    with col2:
        if st.button("Next"):
            if st.session_state.schedule_index < len(valid_schedules) - 1:
                st.session_state.schedule_index += 1

    # Ensure schedule_index is within bounds
    st.session_state.schedule_index = max(0, min(st.session_state.schedule_index, len(valid_schedules) - 1))

    # Get the selected schedule based on the index
    selected_schedule_data = valid_schedules[st.session_state.schedule_index]
    selected_schedule = selected_schedule_data['combo']

    st.write(f"Displaying schedule {st.session_state.schedule_index + 1} of {len(valid_schedules)}")

    # Plot the selected schedule
    st.subheader("Selected Schedule")
    fig = plot_schedule(selected_schedule)
    st.pyplot(fig)

    # Show schedule details
    total_ects = selected_schedule_data['total_ects']
    st.write(f"**Total ECTS**: {total_ects}")
    st.write("**Courses in Schedule:**")
    for code, course in selected_schedule:
        st.write(f"- **{code}** ({course['University']}): {course['ECTS']} ECTS")

    # Display schedule metrics
    st.write("**Schedule Metrics:**")
    st.write(f"- Number of Class Days: {selected_schedule_data['num_days']}")
    st.write(f"- Total Gap Time Between Classes: {selected_schedule_data['gap_time']} hours")
    st.write(f"- Maximum Consecutive Hours: {selected_schedule_data['max_consec']} hours")
    st.write(f"- Earliest Start Time: {selected_schedule_data['earliest_start']}:00")
    st.write(f"- Latest End Time: {selected_schedule_data['latest_end']}:00")
    st.write(f"- Total Penalty: {selected_schedule_data['total_penalty']:.3f}")

    # Implicit Restrictions Section
    st.subheader("Implicit Restrictions")
    st.markdown("""
    - **No Classes from Different Universities on the Same Day**: You cannot have classes from different universities scheduled on the same day.
    - **Maximum 6 Consecutive Hours of Classes per Day**: Schedules with more than 6 consecutive hours of classes on any day are excluded.
    - **No Time Conflicts**: Classes within a schedule do not overlap in time.
    """)

if __name__ == "__main__":
    main()
