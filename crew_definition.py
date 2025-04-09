from crewai import Crew
from agents import agents
from tasks import tasks
from pydantic import BaseModel, Field
from typing import List

# crew = Crew(
#     agents=list(agents.values()),  
#     tasks=list(tasks.values()),   
#     output_pydantic=ProjectPlanOutput,#this should be in task class, can mention in yaml file also. task.output. upgrade to gemini 2.0 flash
#     verbose=True
# )
crew = Crew(
    agents=list(agents.values()),
    tasks=list(tasks.values()),
    verbose=True  # Removed output_pydantic from here
)