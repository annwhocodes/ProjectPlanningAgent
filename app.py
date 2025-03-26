import time
import streamlit as st
import json
from crew_definition import crew
from crew_input import inputs
from trello_utils import get_board_id, get_or_create_list, create_card, update_card_status, save_tasks_to_json, load_tasks_from_json
from litellm.exceptions import RateLimitError

st.set_page_config(page_title="Project Planner AI", layout="wide")

st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan and track it on Trello.")

st.sidebar.header("Project Details")
inputs["project_type"] = st.sidebar.text_input("Project Type", value=inputs["project_type"])
inputs["project_objectives"] = st.sidebar.text_area("Project Objectives", value=inputs["project_objectives"])
inputs["industry"] = st.sidebar.text_input("Industry", value=inputs["industry"])
inputs["team_members"] = st.sidebar.text_area("Team Members", value=inputs["team_members"])
inputs["project_requirements"] = st.sidebar.text_area("Project Requirements", value=inputs["project_requirements"])

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

        structured_tasks = []
        st.subheader("📋 Project Tasks")

        for task in tasks:
            task_name = task.get('task_name', 'No Name')
            assigned_to = task.get('assigned_to', 'Unassigned')
            duration = task.get('duration', 'N/A')

            st.markdown(f"### 🛠️ {task_name}")
            st.write(f"**👨‍💻 Assigned To:** {assigned_to}")
            st.write(f"**⏳ Duration:** {duration}")

            structured_tasks.append({
                "task_name": task_name,
                "assigned_to": assigned_to,
                "duration": duration
            })

            st.write("---")

        save_tasks_to_json(structured_tasks)

        if milestones:
            st.subheader("🎯 Milestones")
            for milestone in milestones:
                st.markdown(f"### 🚀 {milestone.get('milestone_name', 'No Name')}")
                st.write(f"**✅ Tasks Included:** {', '.join(milestone.get('tasks', []))}")

        st.subheader("🔄 Syncing with Trello")

        board_id = get_board_id("My Project Manager Crew")
        if not board_id:
            st.error("❌ Failed to find the Trello board. Make sure 'My Project Manager Crew' exists.")
        else:
            todo_list_id = get_or_create_list(board_id, "To Do")
            in_progress_list_id = get_or_create_list(board_id, "In Progress")
            completed_list_id = get_or_create_list(board_id, "Completed")

            trello_task_ids = {}
            for task in structured_tasks:
                trello_task_name = f"{task['task_name']} - {task['assigned_to']}"
                trello_task_desc = f"Duration: {task['duration']}"
                st.write(f"📌 Adding Task to Trello: {trello_task_name}")

                card_response = create_card(todo_list_id, trello_task_name, trello_task_desc)

                if not card_response or "id" not in card_response:
                    st.error(f"❌ Failed to create Trello card for task: {trello_task_name}")
                    continue

                card_id = card_response["id"]
                trello_task_ids[trello_task_name] = card_id

            st.success("✅ Tasks added to Trello successfully!")

            for task_name, card_id in trello_task_ids.items():
                time.sleep(2)
                st.write(f"⏳ Moving {task_name} to 'In Progress'")
                update_card_status(card_id, in_progress_list_id)

                time.sleep(3)
                st.write(f"✅ Marking {task_name} as 'Completed'")
                update_card_status(card_id, completed_list_id)

            st.success("🎉 Trello board updated with task statuses!")
