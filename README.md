# BlueprintAI - Design your project like an architect – automate the blueprinting process with AI.

BlueprintAI is an **AI-powered project planning assistant** that intelligently breaks down a project into phases, estimates timelines and resources, and allocates team members to tasks. It then syncs everything with **Trello**, enabling streamlined tracking and real-time phase management.

## 🚀 Features

- 📋 **Automated Task Breakdown**  
  Converts project requirements into structured tasks across development phases.

- ⏱️ **Time & Resource Estimation**  
  Estimates duration and human resources required for each task.

- 👥 **Smart Resource Allocation**  
  Assigns roles to your team members based on their strengths and roles.

- ✅ **Trello Integration**  
  Syncs project plans to your Trello board and monitors task completion phase-by-phase.

- 🌐 **Powered by Gemini 1.5 Flash via LiteLLM**  
  Utilizes Google's Gemini LLM for fast and intelligent project planning.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- [Streamlit](https://streamlit.io/)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [LiteLLM](https://docs.litellm.ai/)
- [Google Gemini Flash 1.5](https://ai.google.dev/)
- Trello API

---

## 📦 Setup Instructions

### 1. Clone the Repository

git clone https://github.com/your-username/BlueprintAI.git
cd BlueprintAI

### 2. Create and Activate a Virtual Environment

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

### 3. Install Requirements
pip install -r requirements.txt

### 4. Configure Environment Variables

Create a .env file in the root directory with :

GOOGLE_API_KEY=your_google_generativeai_api_key
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token

### 5.  How to Run the App

streamlit run app.py

Once running, input your project details and let BlueprintAI handle the rest! Watch your Trello board auto-populate and track the progress of each project phase in real time.

### Future Implementations

🔍 Natural language query support for project insights

🧑‍💼 Role optimization based on historical performance

📊 Gantt chart and reporting dashboard

🤝 Slack/Trello/Asana integration expansion