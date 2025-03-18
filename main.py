from crew_definition import crew
from crew_input import inputs

if __name__ == "__main__":
    # Run the crew with structured inputs
    result = crew.kickoff(inputs=inputs)
    
    print("\n🎯 Final Output:")
    print(result.pydantic.dict())  # Print structured output
