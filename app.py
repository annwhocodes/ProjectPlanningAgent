import time 
import streamlit as st
import pandas as pd
from crew_definition import crew 
from crew_input import inputs
from trello_utils import create_board, get_board_id, create_list, create_card, get_list_id, update_card_status
from litellm.exceptions import RateLimitError

# Configure Streamlit page
st.set_page_config(page_title="Project Planner AI", layout="wide")

st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan and track it on Trello.")

# Sidebar for Project Inputs
st.sidebar.header("Project Details")
inputs["project_type"] = st.sidebar.text_input("Project Type", value=inputs["project_type"])
inputs["project_objectives"] = st.sidebar.text_area("Project Objectives", value=inputs["project_objectives"])
inputs["industry"] = st.sidebar.text_input("Industry", value=inputs["industry"])
inputs["team_members"] = st.sidebar.text_area("Team Members", value=inputs["team_members"])
inputs["project_requirements"] = st.sidebar.text_area("Project Requirements", value=inputs["project_requirements"])

# Function to handle retries in case of rate limits
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

# Generate Project Plan
if st.sidebar.button("Generate Project Plan"):
    result = run_crew_with_retry()

    if result:
        tasks = result.get("tasks_output", [])
        milestones = result.get("milestones", [])

        if not tasks:
            st.warning("⚠️ No tasks were generated.")
        if not milestones:
            st.warning("⚠️ No milestones were found.")

        st.success("✅ Project Plan Generated!")

        st.subheader("📌 Project Overview")
        st.markdown(f"""
        **📂 Project Type:** {inputs["project_type"]}  
        **🏭 Industry:** {inputs["industry"]}  
        **🎯 Objective:** {inputs["project_objectives"]}  
        """, unsafe_allow_html=True)

        st.subheader("📋 Project Tasks")

        for task in tasks:
            st.markdown(f"### 🛠️ {task.get('description', 'No Name')}")
            st.write(f"**👨‍💻 Agent:** {task.get('agent', 'Unknown Agent')}")
            st.write(f"**📌 Expected Output:** {task.get('expected_output', 'No Expected Output')}")

            raw_content = task.get('raw', '')
            if raw_content:
                with st.expander(f"📖 View Detailed Breakdown"):
                    st.markdown(raw_content.replace("Task", "🔹 Task").replace("Phase", "## 🚀 Phase"), unsafe_allow_html=True)

            st.write("---") 

        if milestones:
            st.subheader("🎯 Milestones")
            for milestone in milestones:
                st.markdown(f"### 🚀 {milestone.get('milestone_name', 'No Name')}")
                st.write(f"**✅ Tasks Included:** {', '.join(milestone.get('tasks', []))}")

        # ✅ Sync Tasks with Trello
        st.subheader("🔄 Syncing with Trello")

        # Get or create Trello Board
        board_name = f"Project Plan - {inputs['project_type']}"
        board_id = get_board_id(board_name)
        if not board_id:
            st.write(f"📌 Creating Trello Board: {board_name}")
            board_response = create_board(board_name)
            board_id = board_response.get("id")

        # Get or create Trello Lists
        todo_list_id = get_list_id(board_id, "To Do") or create_list(board_id, "To Do")["id"]
        in_progress_list_id = get_list_id(board_id, "In Progress") or create_list(board_id, "In Progress")["id"]
        completed_list_id = get_list_id(board_id, "Completed") or create_list(board_id, "Completed")["id"]

        # Add tasks to Trello
        trello_task_ids = {}
        for task in tasks:
            task_name = task["description"]
            task_desc = f"Planned task for {inputs['project_type']}."
            st.write(f"📌 Adding Task to Trello: {task_name}")

            card_response = create_card(todo_list_id, task_name, task_desc)
            card_id = card_response.get("id")
            if card_id:
                trello_task_ids[task_name] = card_id

        st.success("✅ Tasks added to Trello successfully!")

        # Simulate task progress updates
        for task_name, card_id in trello_task_ids.items():
            time.sleep(2)  # Simulate task progress
            st.write(f"⏳ Moving {task_name} to 'In Progress'")
            update_card_status(card_id, in_progress_list_id)

            time.sleep(3)  # Simulate task completion
            st.write(f"✅ Marking {task_name} as 'Completed'")
            update_card_status(card_id, completed_list_id)
        
        st.success("🎉 Trello board updated with task statuses!")
