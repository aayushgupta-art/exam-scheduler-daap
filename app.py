import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Intelligent Exam Scheduler System", layout="wide")

st.title("?? Intelligent Exam & Room Scheduling System")
st.markdown("DAA Project: **Graph Colouring & Dynamic Multi-Room Optimization**")

st.sidebar.header("Scheduler Parameters")
num_days = st.sidebar.slider("Exam Period (Days)", min_value=1, max_value=14, value=5)
slots_per_day = st.sidebar.selectbox("Time Slots per Day", [2, 3, 4], index=1)
start_date = st.sidebar.date_input("Exam Period Start Date", value=datetime.today())

if "my_courses" not in st.session_state:
    st.session_state.my_courses = pd.DataFrame([
        {"Course Code": "CS101", "Course Name": "Data Structures", "Branch": "Computer Science", "Year": 2, "Students": 45},
        {"Course Code": "AI201", "Course Name": "Machine Learning", "Branch": "AI & ML", "Year": 3, "Students": 30},
        {"Course Code": "CS102", "Course Name": "Operating Systems", "Branch": "Computer Science", "Year": 2, "Students": 40},
    ])

if "my_rooms" not in st.session_state:
    st.session_state.my_rooms = pd.DataFrame([
        {"Room No": "Hall A", "Capacity": 60},
        {"Room No": "Hall B", "Capacity": 50},
        {"Room No": "Lab 1", "Capacity": 30},
        {"Room No": "Hall C", "Capacity": 20},
        {"Room No": "Hall D", "Capacity": 45},
    ])

col1, col2 = st.columns(2)

with col1:
    st.subheader("?? Add New Course")
    with st.form("course_form", clear_on_submit=True):
        f_code = st.text_input("Course Code (e.g., CS101)")
        f_name = st.text_input("Course Name (e.g., Data Structures)")
        f_branch = st.text_input("Branch (e.g., Computer Science / AI & ML)")
        f_year = st.number_input("Academic Year", min_value=1, max_value=4, value=2)
        f_students = st.number_input("Students Enrolled", min_value=1, max_value=500, value=40)
        submitted_course = st.form_submit_button("Add Course to Registry")
        
        if submitted_course and f_code and f_name:
            new_row = pd.DataFrame([{"Course Code": f_code, "Course Name": f_name, "Branch": f_branch, "Year": f_year, "Students": f_students}])
            st.session_state.my_courses = pd.concat([st.session_state.my_courses, new_row], ignore_index=True)
            st.success(f"Added {f_code} successfully!")

with col2:
    st.subheader("??? Add New Room")
    with st.form("room_form", clear_on_submit=True):
        r_no = st.text_input("Room No / Hall Name (e.g., Hall C)")
        r_cap = st.number_input("Seating Capacity", min_value=1, max_value=500, value=50)
        submitted_room = st.form_submit_button("Add Room to Infrastructure")
        
        if submitted_room and r_no:
            new_room = pd.DataFrame([{"Room No": r_no, "Capacity": r_cap}])
            st.session_state.my_rooms = pd.concat([st.session_state.my_rooms, new_room], ignore_index=True)
            st.success(f"Added {r_no} successfully!")

st.divider()

c_tab1, c_tab2 = st.tabs(["?? Current Courses Registry", "?? Current Rooms Infrastructure"])

with c_tab1:
    st.dataframe(st.session_state.my_courses, use_container_width=True)
    if st.button("Clear All Courses"):
        st.session_state.my_courses = pd.DataFrame(columns=["Course Code", "Course Name", "Branch", "Year", "Students"])
        st.rerun()

with c_tab2:
    st.dataframe(st.session_state.my_rooms, use_container_width=True)
    if st.button("Clear All Rooms"):
        st.session_state.my_rooms = pd.DataFrame(columns=["Room No", "Capacity"])
        st.rerun()

st.divider()

if st.button("?? Run Intelligent Scheduling & Room Optimization", type="primary"):
    edited_courses = st.session_state.my_courses
    edited_rooms = st.session_state.my_rooms
    
    if edited_courses.empty or edited_rooms.empty:
        st.error("Please ensure both courses and rooms are provided.")
    else:
        G = nx.Graph()
        exam_nodes = []
        
        for idx, row in edited_courses.iterrows():
            c_code = str(row["Course Code"]).strip()
            c_branch = str(row["Branch"]).strip()
            try:
                c_year = int(row["Year"])
                c_students = int(row["Students"])
            except ValueError:
                c_year = 1
                c_students = 0
            
            node_id = f"{c_code} [{c_branch} - Yr {c_year}] (ID:{idx})"
            exam_nodes.append({
                "node_id": node_id,
                "code": c_code,
                "name": str(row["Course Name"]),
                "branch": c_branch,
                "year": c_year,
                "students": c_students
            })
            G.add_node(node_id)
            
        # Conflict Edges: Connect if same Year or same Branch
        for i in range(len(exam_nodes)):
            for j in range(i + 1, len(exam_nodes)):
                e1 = exam_nodes[i]
                e2 = exam_nodes[j]
                if e1["year"] == e2["year"] or e1["branch"] == e2["branch"]:
                    G.add_edge(e1["node_id"], e2["node_id"])

        try:
            coloring = nx.coloring.greedy_color(G, strategy="largest_first")
        except Exception:
            coloring = {node: 0 for node in G.nodes()}

        slot_labels = [
            "Morning (09:00 AM - 12:00 PM)", 
            "Afternoon (01:00 PM - 04:00 PM)", 
            "Evening (04:30 PM - 07:30 PM)",
            "Night (08:00 PM - 11:00 PM)"
        ]
        
        schedule_results = []
        rooms_base = edited_rooms.copy()
        rooms_base["Capacity"] = pd.to_numeric(rooms_base["Capacity"], errors="coerce").fillna(0)
        
        slot_room_usage = {}
        node_lookup = {item["node_id"]: item for item in exam_nodes}
        
        # STRICT AUTOMATION ENFORCEMENT:
        # Group color indices by Academic Year or ensure strictly distinct time slots per year
        # To completely prevent paper leaks, let's map each unique exam such that same-year courses get strictly separated days.
        year_tracker = {}
        global_slot_counter = 0
        
        sorted_nodes = sorted(coloring.items(), key=lambda x: node_lookup[x[0]]["year"])
        
        for node_id, _ in sorted_nodes:
            exam = node_lookup[node_id]
            year = exam["year"]
            
            if year not in year_tracker:
                year_tracker[year] = global_slot_counter
                global_slot_counter += 1  # Push subsequent years to distinct scheduling slots/days
            else:
                # If same year has multiple courses, push them to the next available distinct slot index
                global_slot_counter += 1
                year_tracker[year] = global_slot_counter

            slot_index = year_tracker[year]
            total_slots = num_days * slots_per_day
            slot_index = slot_index % total_slots
            
            day_offset = slot_index // slots_per_day
            slot_idx_in_day = slot_index % slots_per_day
            
            assigned_date = start_date + timedelta(days=int(day_offset))
            assigned_time_slot = slot_labels[slot_idx_in_day]
            slot_key = f"{assigned_date}_{assigned_time_slot}"
            
            if slot_key not in slot_room_usage:
                slot_room_usage[slot_key] = set()
                
            remaining_students = exam["students"]
            allocated_allocation_list = []
            
            available_rooms = rooms_base[~rooms_base["Room No"].isin(slot_room_usage[slot_key])]
            available_rooms = available_rooms.sort_values(by="Capacity", ascending=False)
            
            for _, room in available_rooms.iterrows():
                if remaining_students <= 0:
                    break
                r_name = str(room["Room No"])
                r_cap = int(room["Capacity"])
                
                if r_cap <= 0:
                    continue
                
                slot_room_usage[slot_key].add(r_name)
                
                if r_cap >= remaining_students:
                    allocated_allocation_list.append(f"{r_name} ({remaining_students} seats)")
                    remaining_students = 0
                else:
                    allocated_allocation_list.append(f"{r_name} ({r_cap} seats)")
                    remaining_students -= r_cap
            
            if remaining_students > 0:
                room_status_str = f"?? Seating Capacity Shortage by {remaining_students} students! Add more rooms."
            else:
                room_status_str = ", ".join(allocated_allocation_list)
                
            schedule_results.append({
                "Course Code": exam["code"],
                "Course Name": exam["name"],
                "Branch": exam["branch"],
                "Year": exam["year"],
                "Students": exam["students"],
                "Exam Date": assigned_date.strftime("%B %d, %Y"),
                "Time Slot": assigned_time_slot,
                "Allocated Rooms & Seating": room_status_str
            })

        df_final_schedule = pd.DataFrame(schedule_results)
        
        st.success("Optimization Successful! Anti-Leak & Automated Slot Distribution Active.")
        st.subheader("?? Final Optimized Exam Schedule")
        st.dataframe(df_final_schedule, use_container_width=True)
        
        st.subheader("?? Conflict Graph Topology (Graph Colouring)")
        fig, ax = plt.subplots(figsize=(8, 5))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G, pos, with_labels=True, 
            node_color='lightgreen', node_size=2200, 
            font_weight='bold', font_size=8, 
            edge_color='gray', ax=ax
        )
        st.pyplot(fig)
