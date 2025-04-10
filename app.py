import time
import threading
import streamlit as st
import json
from crewai import Agent
from crewai import LLM 
from litellm import completion
from typing import Optional, List, Any
import os
from dotenv import load_dotenv
from config_loader import agents_config, tasks_config
from trello_utils import (
    get_board_id,
    load_tasks_from_json,
    parse_allocation_tasks,
    add_tasks_from_allocation,
    check_phase_completion,
    get_or_create_list
)
from agents import project_planning_agent, estimation_agent, resource_allocation_agent, save_allocation_to_json
from crew_definition import crew
from crew_input import inputs
from litellm.exceptions import RateLimitError
from parse_allocation import parse_allocation_plan

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY is missing! Check your .env file.")

class GeminiWrapperLLM(LLM):
    def __init__(self, api_key: str, model: str = "gemini/gemini-1.5-flash"):
        super().__init__(model=model)
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key  

    @property
    def supports_stop_words(self) -> bool:
        return False  

    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = completion(
                model=self.model,
                messages=[{"content": prompt, "role": "user"}],
                api_key=self.api_key,
                temperature=0.7,
                max_tokens=2000,
                **kwargs
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            st.error("⚠️ API rate limit exceeded. Please try again later.")
            return f"Rate limit error: {str(e)}"
        except Exception as e:
            st.error(f"❌ Gemini API Error: {str(e)}")
            return f"API error: {str(e)}"


llm = GeminiWrapperLLM(
    api_key=api_key,
    model="gemini/gemini-1.5-flash"
)


st.set_page_config(page_title="Project Planner AI", layout="wide")
st.title("🛠️ AI-Powered Project Planner")
st.markdown("Use AI to generate a structured project plan and track it on Trello.")




if 'trello_status' not in st.session_state:
    st.session_state.trello_status = ""
if 'syncing' not in st.session_state:
    st.session_state.syncing = False
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = None
if 'phases' not in st.session_state:
    st.session_state.phases = {}



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


def check_phases_background(board_id, phases):
    """Background thread to monitor phase completion and add new phases sequentially"""

    sorted_phases = sorted(phases.keys(), key=int)
    
    if not sorted_phases:
        st.session_state.trello_status = "⚠️ No phases found in tasks!"
        st.session_state.syncing = False
        return
    

    current_phase_index = 0
    

    current_phase = sorted_phases[current_phase_index]
    current_phase_name = f"Phase {current_phase} - Not Started"
    

    st.session_state.current_phase = current_phase
    
 
    add_tasks_from_allocation(board_id, phases[current_phase], current_phase_name)
    st.session_state.trello_status = f"✅ {current_phase_name} tasks added to Trello. Monitoring completion..."
    

    while current_phase_index < len(sorted_phases):
        current_phase = sorted_phases[current_phase_index]
        current_phase_name = f"Phase {current_phase} - Not Started"
        completed_phase_name = f"Phase {current_phase} - Completed"
        

        st.session_state.current_phase = current_phase
        st.session_state.trello_status = f"🔍 Monitoring completion of {current_phase_name}. Checking every 2 minutes..."
        

        while True:
            if check_phase_completion(board_id, current_phase_name):
                get_or_create_list(board_id, completed_phase_name)
                st.session_state.trello_status = f"✅ {current_phase_name} completed!"
                
             
                current_phase_index += 1
                
                if current_phase_index < len(sorted_phases):
                    next_phase = sorted_phases[current_phase_index]
                    next_phase_name = f"Phase {next_phase} - Not Started"
                    
              
                    add_tasks_from_allocation(board_id, phases[next_phase], next_phase_name)
                    st.session_state.current_phase = next_phase
                    st.session_state.trello_status = f"🎉 Started {next_phase_name}. Monitoring completion..."
                else:
                    st.session_state.trello_status = "🎉 All phases completed! Project finished."
                    st.session_state.syncing = False
                    st.session_state.current_phase = None
                    return
                
                break  
            

            time.sleep(120)  


def sync_with_trello(parsed_data, tasks):
    """Start Trello synchronization process"""
    board_id = get_board_id()
    if not board_id:
        st.session_state.trello_status = "❌ Failed to find the Trello board. Make sure 'My Project Manager Crew' exists."
        st.session_state.syncing = False
        return
    
    st.session_state.trello_status = "✅ Connected to Trello board 'My Project Manager Crew'. Starting synchronization..."
    

    phases = parse_allocation_tasks(tasks)
    st.session_state.phases = phases
    

    sync_thread = threading.Thread(
        target=check_phases_background,
        args=(board_id, phases),
        daemon=True
    )
    sync_thread.start()


def ensure_fields_present(task):
    """Ensure all required fields are present in task data, with proper formatting"""

    if "assigned_to" in task:
        if isinstance(task["assigned_to"], list):
            task["assigned_to"] = ", ".join(task["assigned_to"])
        elif task["assigned_to"] is None:
            task["assigned_to"] = "Unassigned"
    else:
        task["assigned_to"] = "Unassigned"
    

    if "duration" not in task or not task["duration"]:
        task["duration"] = "N/A"
    

    if "resources" not in task or not task["resources"]:
        task["resources"] = []
    
    return task


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
            

            st.write("Debug - Parsed data structure:", parsed_data)
            
            for phase in parsed_data.get("phases", []):
                for task in phase.get("tasks", []):
    
                    task = ensure_fields_present(task)
                    
                    tasks.append({
                        "task_name": f"{task.get('task_id', 'Task')} - {task.get('task_name', 'Unnamed Task')}",
                        "assigned_to": task["assigned_to"],
                        "duration": task["duration"],
                        "resources": task.get("resources", []),
                        "phase": f"{phase.get('phase_number', '0')}. {phase.get('phase_name', 'Unnamed Phase')}"
                    })

            st.write("Debug - Tasks before saving:", tasks)
            
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