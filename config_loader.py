import yaml

# Function to load YAML files
def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

# Load Agents and Tasks
agents_config = load_yaml("config/agents.yaml")
tasks_config = load_yaml("config/tasks.yaml")
