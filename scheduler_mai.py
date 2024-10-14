import json
import streamlit as st
from itertools import combinations
import matplotlib.pyplot as plt

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

def get_number_of_class_days(course_combination):
    days_with_classes = set()
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            days_with_classes.add(slot['day'])
    return len(days_with_classes)

def total_class_hours(course_combination):
    total_hours = 0
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            total_hours += slot['end'] - slot['start']
    return total_hours

def total_credits(course_combination):
    return sum(course['ECTS'] for code, course in course_combination)

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
    days = {}
    for code, course in course_combination:
        for slot in course['parsed_schedule']:
            day = slot['day']
            if day not in days:
                days[day] = []
            days[day].append(slot)
    max_consecutive = 0
    for slots in days.values():
        slots.sort(key=lambda x: x['start'])
        # Merge overlapping or consecutive slots
        merged_slots = []
        current_slot = slots[0].copy()
        for slot in slots[1:]:
            if slot['start'] <= current_slot['end']:
                # Overlapping or consecutive slots
                current_slot['end'] = max(current_slot['end'], slot['end'])
            elif slot['start'] == current_slot['end']:
                # Consecutive slots
                current_slot['end'] = slot['end']
            else:
                # Gap between slots
                merged_slots.append(current_slot)
                current_slot = slot.copy()
        merged_slots.append(current_slot)
        # Find the longest merged slot
        day_max_consecutive = max(slot['end'] - slot['start'] for slot in merged_slots)
        if day_max_consecutive > max_consecutive:
            max_consecutive = day_max_consecutive
    return max_consecutive

def generate_valid_schedules(courses, min_credits, max_credits, max_days):
    valid_schedules = []
    course_items = list(courses.items())
    N = len(course_items)
    for r in range(1, N+1):
        for course_combination in combinations(course_items, r):
            total_ects = total_credits(course_combination)
            if min_credits <= total_ects <= max_credits:
                if combination_has_no_conflicts(course_combination):
                    if combination_respects_university_day_rule(course_combination):
                        num_class_days = get_number_of_class_days(course_combination)
                        if num_class_days <= max_days:
                            valid_schedules.append({
                                'combo': course_combination,
                                'num_days': num_class_days,
                                'gap_time': total_gap_time(course_combination),
                                'max_consec': max_consecutive_hours(course_combination),
                                'total_hours': total_class_hours(course_combination),
                                'total_ects': total_credits(course_combination),
                            })
    return valid_schedules

def plot_schedule(course_combination):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    fig, ax = plt.subplots(figsize=(10, 6))

    # Prepare colors
    colors = plt.cm.get_cmap('tab20', len(course_combination))
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
                slot['start'] + 0.5,
                f"{code}\n{slot['class_type']}",
                ha='center', va='bottom', color='white', fontsize=8
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
        max_value=30.0,
        value=(0.0, 30.0),
        step=0.5
    )

    # Ranking weights
    st.sidebar.header("Ranking Weights")
    w_num_days = st.sidebar.slider("Weight for Number of Class Days", 0.0, 1.0, 0.3)
    w_gap_time = st.sidebar.slider("Weight for Total Gap Time", 0.0, 1.0, 0.3)
    w_max_consecutive = st.sidebar.slider("Weight for Max Consecutive Hours", 0.0, 1.0, 0.4)

    # Normalize weights to sum to 1
    total_weight = w_num_days + w_gap_time + w_max_consecutive
    if total_weight > 0:
        w_num_days /= total_weight
        w_gap_time /= total_weight
        w_max_consecutive /= total_weight
    else:
        st.error("At least one weight must be greater than zero.")
        return

    # Filter courses
    filtered_courses = {
        code: course for code, course in data.items()
        if course['University'] in selected_universities
    }

    # Generate valid schedules
    valid_schedules = generate_valid_schedules(
        filtered_courses, min_credits, max_credits, max_days_per_week)

    if not valid_schedules:
        st.warning("No valid schedules found with the given criteria.")
        return

    # Compute min and max for normalization
    num_days_values = [s['num_days'] for s in valid_schedules]
    gap_time_values = [s['gap_time'] for s in valid_schedules]
    max_consec_values = [s['max_consec'] for s in valid_schedules]

    min_num_days = min(num_days_values)
    max_num_days = max(num_days_values)
    min_gap_time = min(gap_time_values)
    max_gap_time = max(gap_time_values)
    min_max_consec = min(max_consec_values)
    max_max_consec = max(max_consec_values)

    # Normalize and compute scores
    for s in valid_schedules:
        # Normalize num_days
        if max_num_days - min_num_days > 0:
            s['norm_num_days'] = (s['num_days'] - min_num_days) / (max_num_days - min_num_days)
        else:
            s['norm_num_days'] = 0.0
        # Normalize gap_time
        if max_gap_time - min_gap_time > 0:
            s['norm_gap_time'] = (s['gap_time'] - min_gap_time) / (max_gap_time - min_gap_time)
        else:
            s['norm_gap_time'] = 0.0
        # Normalize max_consec
        if max_max_consec - min_max_consec > 0:
            s['norm_max_consec'] = (s['max_consec'] - min_max_consec) / (max_max_consec - min_max_consec)
        else:
            s['norm_max_consec'] = 0.0
        # Compute score
        s['score'] = (
            w_num_days * s['norm_num_days'] +
            w_gap_time * s['norm_gap_time'] +
            w_max_consecutive * s['norm_max_consec']
        )

    # Sort schedules
    valid_schedules.sort(key=lambda s: s['score'])
    selected_schedule_data = valid_schedules[0]
    selected_schedule = selected_schedule_data['combo']

    st.success(f"Found {len(valid_schedules)} valid schedules.")

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
    st.write(f"- Score: {selected_schedule_data['score']:.3f}")

if __name__ == "__main__":
    main()
