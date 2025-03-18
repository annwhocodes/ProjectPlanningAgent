import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# ✅ Load API Key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# ✅ Check if API Key is Loaded
if not api_key:
    raise ValueError("❌ GROQ_API_KEY is missing! Ensure it is set in the .env file.")

# ✅ Initialize Groq Model
try:
    llm = ChatGroq(
        model="llama3-8b-8192",  # ✅ Ensure correct model name
        api_key=api_key
    )

    # ✅ Test LLM Call
    response = llm.invoke("Tell me a fun fact about space.")

    print("\n✅ API Key is working!")
    print("🚀 Model Response:", response)

except Exception as e:
    print("\n❌ API Call Failed!")
    print("Error:", str(e))
