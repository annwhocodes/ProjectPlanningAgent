from crewai import Agent
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from config_loader import agents_config  

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

agents = {}
for key, config in agents_config.items():
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
