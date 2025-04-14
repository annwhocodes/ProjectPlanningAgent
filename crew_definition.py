# crew = Crew(
#     agents=list(agents.values()),  
#     tasks=list(tasks.values()),   
#     output_pydantic=ProjectPlanOutput,#this should be in task class, can mention in yaml file also. task.output. upgrade to gemini 2.0 flash
#     verbose=True
# )
from crewai import Crew, Process
from agents import project_planning_agent, estimation_agent, resource_allocation_agent
from tasks import tasks
from config_loader import tasks_config

crew = Crew(
    agents=[project_planning_agent, estimation_agent, resource_allocation_agent],
    tasks=[
        tasks_config["task_breakdown"],
        tasks_config["time_resource_estimation"],
        tasks_config["resource_allocation"]
    ],
    verbose=2,
    process=Process.sequential,
    memory=False
)