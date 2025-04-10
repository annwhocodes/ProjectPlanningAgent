from crewai import Agent
import os
import json
from dotenv import load_dotenv
from config_loader import agents_config
from gemini_wrapper import GeminiWrapperLLM


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY is missing! Check your .env file.")


print(f"API key found, length: {len(api_key)}")


llm = GeminiWrapperLLM(
    api_key=api_key,
    model="gemini/gemini-1.5-flash"
)

JSON_FILE = "allocation_tasks.json"

def save_allocation_to_json(parsed_data, output_file=JSON_FILE):
    """
    Save the parsed tasks to a JSON file
    
    Args:
        parsed_data (dict): Parsed data with phases and tasks
        output_file (str): Path to the output JSON file
    """
    try:
        with open(output_file, "w") as f:
            json.dump(parsed_data, f, indent=4)
        print(f"✅ Tasks saved to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving allocation to JSON: {str(e)}")
        return False


print("DEBUG: agents_config structure:", agents_config)


agents = {}


if not agents_config or not isinstance(agents_config, dict):
    raise ValueError("❌ Failed to load agents configuration correctly")

for key, config in agents_config.items():
    print(f"Creating agent: {key}")
    print(f"Config: {config}")
    
    if not all(k in config for k in ["role", "goal", "backstory"]):
        raise ValueError(f"❌ Missing required configuration for agent {key}")
    
    agents[key] = Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        verbose=config.get("verbose", True),
        llm=llm
    )

project_planning_agent = agents.get("project_planning_agent")
estimation_agent = agents.get("estimation_agent")
resource_allocation_agent = agents.get("resource_allocation_agent")

print("Created agents:", list(agents.keys()))