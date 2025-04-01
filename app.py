import time
import threading
import streamlit as st
import json
from trello_utils import (
    get_board_id,
    load_tasks_from_json,
    parse_allocation_tasks,
    add_tasks_from_allocation,
    check_phase_completion,
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
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = None
if 'phases' not in st.session_state:
    st.session_state.phases = {}

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


def check_phases_background(board_id, phases):
    """Background thread to monitor phase completion and add new phases sequentially"""
    # Get sorted phase numbers
    sorted_phases = sorted(phases.keys(), key=int)
    
    if not sorted_phases:
        st.session_state.trello_status = "⚠️ No phases found in tasks!"
        st.session_state.syncing = False
        return
    
    # Start with the first phase
    current_phase_index = 0
    
    # Add first phase tasks to Trello
    current_phase = sorted_phases[current_phase_index]
    current_phase_name = f"Phase {current_phase} - Not Started"
    
    # Store current phase in session state for display
    st.session_state.current_phase = current_phase
    
    # Add tasks for first phase
    add_tasks_from_allocation(board_id, phases[current_phase], current_phase_name)
    st.session_state.trello_status = f"✅ {current_phase_name} tasks added to Trello. Monitoring completion..."
    
    # Process phases sequentially
    while current_phase_index < len(sorted_phases):
        current_phase = sorted_phases[current_phase_index]
        current_phase_name = f"Phase {current_phase} - Not Started"
        completed_phase_name = f"Phase {current_phase} - Completed"
        
        # Update session state
        st.session_state.current_phase = current_phase
        st.session_state.trello_status = f"🔍 Monitoring completion of {current_phase_name}. Checking every 2 minutes..."
        
        # Wait until current phase is complete
        while True:
            if check_phase_completion(board_id, current_phase_name):
                # Create completed list for this phase
                get_or_create_list(board_id, completed_phase_name)
                st.session_state.trello_status = f"✅ {current_phase_name} completed!"
                
                # Move to next phase
                current_phase_index += 1
                
                if current_phase_index < len(sorted_phases):
                    next_phase = sorted_phases[current_phase_index]
                    next_phase_name = f"Phase {next_phase} - Not Started"
                    
                    # Add tasks for next phase
                    add_tasks_from_allocation(board_id, phases[next_phase], next_phase_name)
                    st.session_state.current_phase = next_phase
                    st.session_state.trello_status = f"🎉 Started {next_phase_name}. Monitoring completion..."
                else:
                    st.session_state.trello_status = "🎉 All phases completed! Project finished."
                    st.session_state.syncing = False
                    st.session_state.current_phase = None
                    return
                
                break  # Exit the inner while loop to start monitoring the next phase
            
            # Wait before checking again
            time.sleep(120)  # Check every 2 minutes


def sync_with_trello(parsed_data, tasks):
    """Start Trello synchronization process"""
    board_id = get_board_id()
    if not board_id:
        st.session_state.trello_status = "❌ Failed to find the Trello board. Make sure 'My Project Manager Crew' exists."
        st.session_state.syncing = False
        return
    
    st.session_state.trello_status = "✅ Connected to Trello board 'My Project Manager Crew'. Starting synchronization..."
    
    # Parse tasks into phases
    phases = parse_allocation_tasks(tasks)
    st.session_state.phases = phases
    
    # Start background monitoring thread
    sync_thread = threading.Thread(
        target=check_phases_background,
        args=(board_id, phases),
        daemon=True
    )
    sync_thread.start()


if st.sidebar.button("Generate Project Plan"):
    result = run_crew_with_retry()
    if result:
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


# Display Trello synchronization status
if st.session_state.syncing:
    st.subheader("🔄 Trello Synchronization Status")
    st.info(st.session_state.trello_status)
    
    # Show current phase information if available
    if st.session_state.current_phase and st.session_state.phases:
        current_phase = st.session_state.current_phase
        phase_tasks = st.session_state.phases.get(current_phase, [])
        
        st.subheader(f"Current Phase: {current_phase}")
        if phase_tasks:
            st.write(f"Tasks in this phase: {len(phase_tasks)}")
            for task in phase_tasks:
                st.write(f"- {task.get('task_name')} (Assigned to: {task.get('assigned_to')})")
    
    if st.button("Refresh Status"):
        st.rerun()