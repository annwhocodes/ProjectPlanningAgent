import time
import streamlit as st
import pandas as pd
from crew_definition import crew  # Import CrewAI
from crew_input import inputs
from litellm.exceptions import RateLimitError

st.set_page_config(page_title="Project Planner AI", layout="wide")

st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan.")

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
                result = crew.kickoff(inputs=inputs)  # Directly use `crew.kickoff()`
            return result.dict()  # Convert structured output to dictionary
        except RateLimitError:
            wait_time = 10 * (attempt + 1)
            st.warning(f"🚨 Rate Limit Exceeded! Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            st.error(f"❌ Error running CrewAI: {str(e)}")
            return None
    st.error("❌ Crew execution failed after multiple attempts. Try again later.")
    return None

if st.sidebar.button("Generate Project Plan"):
    result = run_crew_with_retry()

    if result:
        # ✅ Extract tasks from "tasks_output"
        tasks = result.get("tasks_output", [])  # Use the correct key
        milestones = result.get("milestones", [])

        if not tasks:
            st.warning("⚠️ No tasks were generated.")
        if not milestones:
            st.warning("⚠️ No milestones were found.")

        st.success("✅ Project Plan Generated!")

        # ✅ Display Project Overview
        st.subheader("📌 Project Overview")
        st.markdown(f"""
        **📂 Project Type:** {inputs["project_type"]}  
        **🏭 Industry:** {inputs["industry"]}  
        **🎯 Objective:** {inputs["project_objectives"]}  
        """, unsafe_allow_html=True)

        # ✅ Display Tasks with Expandable Sections
        st.subheader("📋 Project Tasks")

        for task in tasks:
            st.markdown(f"### 🛠️ {task.get('description', 'No Name')}")
            st.write(f"**👨‍💻 Agent:** {task.get('agent', 'Unknown Agent')}")
            st.write(f"**📌 Expected Output:** {task.get('expected_output', 'No Expected Output')}")

            # ✅ Display task breakdown in an expandable section
            raw_content = task.get('raw', '')
            if raw_content:
                with st.expander(f"📖 View Detailed Breakdown"):
                    st.markdown(raw_content.replace("Task", "🔹 Task").replace("Phase", "## 🚀 Phase"), unsafe_allow_html=True)

            st.write("---")  # Separator

        # ✅ Display Milestones if Available
        if milestones:
            st.subheader("🎯 Milestones")
            for milestone in milestones:
                st.markdown(f"### 🚀 {milestone.get('milestone_name', 'No Name')}")
                st.write(f"**✅ Tasks Included:** {', '.join(milestone.get('tasks', []))}")

