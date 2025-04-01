import time
import threading
import streamlit as st
import json
from trello_utils import (
    get_board_id,
    load_tasks_from_json,
    parse_allocation_tasks,
    add_tasks_from_allocation,
    check_phase_1_completion,
    get_or_create_list
)
from agents import save_allocation_to_json
from crew_definition import crew
from crew_input import inputs
from litellm.exceptions import RateLimitError
from parse_allocation import parse_allocation_plan

st.set_page_config(page_title="Project Planner AI", layout="wide")
st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan and track it on Trello.")

# Initialize session state variables
if 'trello_status' not in st.session_state:
    st.session_state.trello_status = ""
if 'syncing' not in st.session_state:
    st.session_state.syncing = False

# Sidebar for Project Details
st.sidebar.header("Project Details")
inputs["project_type"] = st.sidebar.text_input("Project Type", value=inputs["project_type"])
inputs["project_objectives"] = st.sidebar.text_area("Project Objectives", value=inputs["project_objectives"])
inputs["industry"] = st.sidebar.text_input("Industry", value=inputs["industry"])
inputs["team_members"] = st.sidebar.text_area("Team Members", value=inputs["team_members"])
inputs["project_requirements"] = st.sidebar.text_area("Project Requirements", value=inputs["project_requirements"])

# Function to run Crew with retry logic for rate limits
def run_crew_with_retry():
    retries = 3
    for attempt in range(retries):
        try:
            with st.spinner("🔄 Running AI Agents..."):
                result = crew.kickoff(inputs=inputs)
            return result.dict()
        except RateLimitError:
            wait_time = 10 * (attempt + 1)
            st.warning(f"🚨 Rate Limit Exceeded! Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            st.error(f"❌ Error running CrewAI: {str(e)}")
            return None
    st.error("Crew execution failed after multiple attempts. Try again later.")
    return None


def check_phase_1_completion_background(board_id, tasks):
    phase_1_tasks, phase_2_tasks = parse_allocation_tasks(tasks)
    
    # Add Phase 1 tasks to Trello
    phase_1_list_id = get_or_create_list(board_id, "Phase 1 - Not Started")
    add_tasks_from_allocation(board_id, phase_1_tasks, "Phase 1 - Not Started")
    
    # Update session state to show user what's happening
    st.session_state.trello_status = "✅ Phase 1 tasks added to Trello. Checking completion every 2 minutes..."
    
    # Keep checking until complete
    while True:
        # Check if all Phase 1 tasks are marked as completed
        if check_phase_1_completion(board_id, "Phase 1 - Not Started"):
            # Add Phase 2 tasks
            phase_2_list_id = get_or_create_list(board_id, "Phase 2 - Not Started")
            add_tasks_from_allocation(board_id, phase_2_tasks, "Phase 2 - Not Started")
            st.session_state.trello_status = "🎉 Phase 1 tasks completed! Phase 2 tasks added to Trello."
            st.session_state.syncing = False
            break
        
        time.sleep(120)  

def sync_with_trello(parsed_data, tasks):
    board_id = get_board_id()  
    if not board_id:
        st.session_state.trello_status = "❌ Failed to find the Trello board. Make sure 'My Project Manager Crew' exists."
        st.session_state.syncing = False
        return
    
    st.session_state.trello_status = f"✅ Connected to Trello board 'My Project Manager Crew'. Starting synchronization..."
    

    sync_thread = threading.Thread(
        target=check_phase_1_completion_background,
        args=(board_id, tasks),
        daemon=True
    )
    sync_thread.start()


if st.sidebar.button("Generate Project Plan"):
    result = run_crew_with_retry()
    if result:
        st.write("Debug - Raw Result Structure:", result)

        raw_alloc = None
        if "tasks_output" in result and isinstance(result["tasks_output"], list):
            for task_output in result["tasks_output"]:
                if isinstance(task_output, dict) and task_output.get("agent") == "Resource Allocator":
                    raw_alloc = task_output.get("raw")
                    break
        
        if raw_alloc:
            st.text_area("Raw Allocation Output", raw_alloc, height=200)

            parsed_data = parse_allocation_plan(raw_alloc)
            tasks = []
            
            for phase in parsed_data.get("phases", []):
                for task in phase.get("tasks", []):
                    tasks.append({
                        "task_name": f"{task['task_id']} - {task['task_name']}",
                        "assigned_to": ", ".join(task["assigned_to"]) if isinstance(task["assigned_to"], list) else task["assigned_to"],
                        "duration": task["duration"],
                        "resources": task.get("resources", []),
                        "phase": f"{phase['phase_number']}. {phase['phase_name']}"
                    })

            save_allocation_to_json(tasks)

            st.success("✅ Project Plan Generated!")
            st.subheader("📌 Project Overview")
            st.markdown(f"""
            **📂 Project Type:** {inputs["project_type"]}  
            **🏭 Industry:** {inputs["industry"]}  
            **🎯 Objective:** {inputs["project_objectives"]}  
            """, unsafe_allow_html=True)
            
            st.subheader("📋 Project Tasks")
            for task in tasks:
                st.markdown(f"### 🛠️ {task['task_name']}")
                st.write(f"**👨‍💻 Assigned To:** {task['assigned_to']}")
                st.write(f"**⏳ Duration:** {task['duration']}")
                if task.get("resources"):
                    st.write(f"**👥 Resources:** {', '.join(task['resources'])}")
                st.write(f"**📌 Phase:** {task['phase']}")
                st.write("---")


            if not st.session_state.syncing:
                st.session_state.syncing = True
                sync_with_trello(parsed_data, tasks)

        else:
            st.warning("⚠️ No resource allocation output was generated.")
            st.write("Debug - Full result object:", result)


if st.session_state.syncing:
    st.subheader("🔄 Trello Synchronization Status")
    st.info(st.session_state.trello_status)
    

    if st.button("Refresh Status"):
        st.rerun()