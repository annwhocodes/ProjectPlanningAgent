import yaml
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')

def load_yaml_config(file_path):
    """Load YAML configuration file"""
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config file {file_path}: {str(e)}")
        return {}


agents_config_path = os.path.join(CONFIG_DIR, 'agents.yaml')
if not os.path.exists(agents_config_path):
    agents_config_path = os.path.join(os.path.dirname(__file__), 'agents.yaml')


tasks_config_path = os.path.join(CONFIG_DIR, 'tasks.yaml')
if not os.path.exists(tasks_config_path):
    tasks_config_path = os.path.join(os.path.dirname(__file__), 'tasks.yaml')


agents_config = load_yaml_config(agents_config_path)
tasks_config = load_yaml_config(tasks_config_path)


print(f"Loaded agents config from: {agents_config_path}")
print(f"Loaded tasks config from: {tasks_config_path}")