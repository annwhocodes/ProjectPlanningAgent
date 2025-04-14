from crewai import Task
from agents import agents
from config_loader import tasks_config
from typing import Optional, List, Dict, Any

# If you have project_models.py with Pydantic models:
# from project_models import TaskOutput, ProjectPlanOutput

# Create tasks without depending on Pydantic models for now
tasks = {}

for key, config in tasks_config.items():
    agent_key = config["agent"]
    
    tasks[key] = Task(
        description=config["description"],
        agent=agents[agent_key],
        expected_output=config["expected_output"],
    )

task_breakdown = tasks.get("task_breakdown")
time_resource_estimation = tasks.get("time_resource_estimation")
resource_allocation = tasks.get("resource_allocation")