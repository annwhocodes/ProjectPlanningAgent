from pydantic import BaseModel, Field
from typing import List

class Resource(BaseModel):
    """Resource allocation for a specific task"""
    name: str = Field(..., description="Name of the team member")
    role: str = Field(..., description="Role of the team member")
    duration: int = Field(..., description="Duration in days")

class Task(BaseModel):
    """Task with resource allocations"""
    task_id: str = Field(..., description="Task identifier (e.g., '1.1')")
    task_name: str = Field(..., description="Name of the task")
    resources: List[Resource] = Field(default_factory=list, description="Resources allocated to this task")

    def total_days(self) -> int:
        """Calculate the total days required for this task"""
        return sum(resource.duration for resource in self.resources)

    def assigned_roles(self) -> List[str]:
        """Get unique list of roles assigned to this task"""
        return list(set(resource.role for resource in self.resources))

class Phase(BaseModel):
    """Project phase containing multiple tasks"""
    phase_number: int = Field(..., description="Phase number")
    phase_name: str = Field(..., description="Name of the phase")
    tasks: List[Task] = Field(default_factory=list, description="Tasks in this phase")

    def total_days(self) -> int:
        """Calculate the total days required for this phase"""
        return sum(task.total_days() for task in self.tasks)

class ResourceAllocationPlan(BaseModel):
    """Complete resource allocation plan with multiple phases"""
    phases: List[Phase] = Field(default_factory=list, description="Project phases")

    def total_days(self) -> int:
        """Calculate the total days required for the entire project"""
        return sum(phase.total_days() for phase in self.phases)

    def formatted_allocation_output(self) -> str:
        """Generate resource allocation output in the required format"""
        output = []
        for phase in self.phases:
            output.append(f"**Phase {phase.phase_number}: {phase.phase_name}**\n")
            for task in phase.tasks:
                output.append(f"* Task {task.task_id}: {task.task_name}")
                for role in task.assigned_roles():
                    total_days = sum(res.duration for res in task.resources if res.role == role)
                    output.append(f"\t+ Assigned to: {role}")
                    output.append(f"\t+ Estimated time: {total_days} days")
                output.append("")  # Add a blank line between tasks

        return "\n".join(output)
