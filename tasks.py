from crewai import Task
from agents import agents  
from config_loader import tasks_config 


tasks = {}
for key, config in tasks_config.items():
    agent_key = config["agent"]
    tasks[key] = Task(
        description=config["description"],
        agent=agents[agent_key], 
        expected_output=config["expected_output"]
    )

task_breakdown = tasks["task_breakdown"]
time_resource_estimation = tasks["time_resource_estimation"]
resource_allocation = tasks["resource_allocation"]
