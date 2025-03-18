import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing! Ensure it is set in the .env file.")


try:
    llm = ChatGroq(
        model="llama3-8b-8192", 
        api_key=api_key
    )

    response = llm.invoke("Tell me a fun fact about space.")

    print("\n API Key is working!")
    print(" Model Response:", response)

except Exception as e:
    print("\n API Call Failed!")
    print("Error:", str(e))
