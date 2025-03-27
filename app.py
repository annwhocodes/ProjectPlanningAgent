import time
import streamlit as st
import json
from crew_definition import crew
from crew_input import inputs
from trello_utils import get_board_id, get_or_create_list, create_card, update_card_status, save_tasks_to_json, load_tasks_from_json
from litellm.exceptions import RateLimitError
from parse_allocation import parse_allocation_plan

# Initialize Streamlit app
st.set_page_config(page_title="Project Planner AI", layout="wide")
st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan and track it on Trello.")

# Sidebar inputs
st.sidebar.header("Project Details")
inputs["project_type"] = st.sidebar.text_input("Project Type", value=inputs["project_type"])
inputs["project_objectives"] = st.sidebar.text_area("Project Objectives", value=inputs["project_objectives"])
inputs["industry"] = st.sidebar.text_input("Industry", value=inputs["industry"])
inputs["team_members"] = st.sidebar.text_area("Team Members", value=inputs["team_members"])
inputs["project_requirements"] = st.sidebar.text_area("Project Requirements", value=inputs["project_requirements"])

def run_crew_with_retry():
    """Run the crew with retry logic for rate limits."""
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

if st.sidebar.button("Generate Project Plan"):
    result = run_crew_with_retry()
    if result:
        # Debug: Show the raw result structure
        st.write("Debug - Raw Result Structure:", result)
        
        # Extract the resource allocation output from tasks_output
        raw_alloc = None
        if "tasks_output" in result and isinstance(result["tasks_output"], list):
            for task_output in result["tasks_output"]:
                if isinstance(task_output, dict) and task_output.get("agent") == "Resource Allocator":
                    raw_alloc = task_output.get("raw")
                    break
        
        if raw_alloc:
            # Show the raw output for debugging
            st.text_area("Raw Allocation Output", raw_alloc, height=200)
            
            # Parse the allocation output
            parsed_data = parse_allocation_plan(raw_alloc)
            tasks = []
            
            # Extract tasks from the parsed phases
            for phase in parsed_data.get("phases", []):
                for task in phase.get("tasks", []):
                    tasks.append({
                        "task_name": f"{task['task_id']} - {task['task_name']}",
                        "assigned_to": ", ".join(task["assigned_to"]) if isinstance(task["assigned_to"], list) else task["assigned_to"],
                        "duration": task["duration"],
                        "resources": task.get("resources", []),
                        "phase": f"{phase['phase_number']}. {phase['phase_name']}"
                    })
            
            # Save the structured tasks to JSON
            save_tasks_to_json(tasks)
            
            # Display the results
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
            
            # Sync with Trello
            st.subheader("🔄 Syncing with Trello")
            board_id = get_board_id("My Project Manager Crew")
            if not board_id:
                st.error("❌ Failed to find the Trello board. Make sure 'My Project Manager Crew' exists.")
            else:
                # Create lists for each phase
                phase_lists = {}
                for phase in parsed_data.get("phases", []):
                    list_name = f"{phase['phase_number']}. {phase['phase_name']}"
                    list_id = get_or_create_list(board_id, list_name)
                    if list_id:
                        phase_lists[phase['phase_number']] = list_id
                
                # Create standard lists
                todo_list_id = get_or_create_list(board_id, "To Do")
                in_progress_list_id = get_or_create_list(board_id, "In Progress")
                completed_list_id = get_or_create_list(board_id, "Completed")
                
                trello_task_ids = {}
                for task in tasks:
                    trello_task_desc = (
                        f"Assigned to: {task['assigned_to']}\n"
                        f"Duration: {task['duration']}\n"
                        f"Phase: {task['phase']}"
                    )
                    if task.get("resources"):
                        trello_task_desc += f"\nResources: {', '.join(task['resources'])}"
                    
                    # Determine which list to add the card to
                    target_list_id = phase_lists.get(int(task['phase'].split('.')[0]), todo_list_id)
                    
                    st.write(f"📌 Adding Task to Trello: {task['task_name']}")
                    card_response = create_card(target_list_id, task['task_name'], trello_task_desc)
                    
                    if not card_response or "id" not in card_response:
                        st.error(f"❌ Failed to create Trello card for task: {task['task_name']}")
                        continue
                    
                    card_id = card_response["id"]
                    trello_task_ids[task['task_name']] = card_id
                
                st.success("✅ Tasks added to Trello successfully!")
                
                # Optional: Move some tasks through workflow for demo
                demo_tasks = list(trello_task_ids.items())[:3]  # Just demo with first 3 tasks
                for task_name, card_id in demo_tasks:
                    time.sleep(2)
                    st.write(f"⏳ Moving {task_name} to 'In Progress'")
                    update_card_status(card_id, in_progress_list_id)
                    time.sleep(3)
                    st.write(f"✅ Marking {task_name} as 'Completed'")
                    update_card_status(card_id, completed_list_id)
                
                st.success("🎉 Trello board updated with task statuses!")
        else:
            st.warning("⚠️ No resource allocation output was generated.")
            st.write("Debug - Full result object:", result)  # Show full result for debugging