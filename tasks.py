from crewai import Task
from agents import agents  # Loaded dynamically
from config_loader import tasks_config  # Load YAML configs

# Create Tasks dynamically from YAML
tasks = {}
for key, config in tasks_config.items():
    agent_key = config["agent"]
    tasks[key] = Task(
        description=config["description"],
        agent=agents[agent_key],  # Assign agent dynamically
        expected_output=config["expected_output"]
    )

# Unpack tasks for direct use
task_breakdown = tasks["task_breakdown"]
time_resource_estimation = tasks["time_resource_estimation"]
resource_allocation = tasks["resource_allocation"]
