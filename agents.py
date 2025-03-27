# agents.py
from crewai import Agent
from langchain_groq import ChatGroq
import os
import json
from dotenv import load_dotenv
from config_loader import agents_config
from parse_allocation import parse_allocation_plan 

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ GROQ_API_KEY is missing! Check your .env file.")

llm = ChatGroq(
    model="groq/llama3-8b-8192",
    api_key=api_key,
    temperature=0.7,
    max_tokens=500
)

JSON_FILE = "allocation_tasks.json"

def save_allocation_to_json(allocation_output):
    try:
        with open(JSON_FILE, "w") as f:
            json.dump(allocation_output, f, indent=4)
        print(f"✅ Allocation plan saved to {JSON_FILE}")
    except Exception as e:
        print(f"❌ Error saving allocation to JSON: {str(e)}")

class ResourceAllocationAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def generate_allocation_plan(self, raw_output):
        # Just return the raw output - parsing will happen in app.py
        return {
            "resource_allocation_output": raw_output,
            "status": "success"
        }

# Initialize agents
agents = {}
for key, config in agents_config.items():
    if key == "resource_allocation_agent":
        agents[key] = ResourceAllocationAgent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config["verbose"],
            llm=llm
        )
    else:
        agents[key] = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config["verbose"],
            llm=llm
        )

project_planning_agent = agents["project_planning_agent"]
estimation_agent = agents["estimation_agent"]
resource_allocation_agent = agents["resource_allocation_agent"]