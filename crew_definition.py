from crewai import Crew
from agents import agents
from tasks import tasks
from pydantic import BaseModel, Field
from typing import List


class TaskOutput(BaseModel):
    task_name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Detailed task description")

class MilestoneOutput(BaseModel):
    milestone_name: str = Field(..., description="Name of the milestone")
    tasks: List[str] = Field(..., description="Tasks linked to this milestone")

class ProjectPlanOutput(BaseModel):
    tasks: List[TaskOutput] = Field(..., description="List of tasks with descriptions")
    milestones: List[MilestoneOutput] = Field(..., description="List of project milestones")

crew = Crew(
    agents=list(agents.values()),  # Load all agents from YAML
    tasks=list(tasks.values()),    # Load all tasks from YAML
    output_pydantic=ProjectPlanOutput,  # ✅ Return structured output
    verbose=True
)
