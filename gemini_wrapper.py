from crewai import LLM
from litellm import completion
import os
from typing import Optional
# Turn on debug mode for LiteLLM
import litellm
litellm._turn_on_debug()

class GeminiWrapperLLM(LLM):
    def __init__(self, api_key: str, model: str = "gemini/gemini-1.5-flash"):
        super().__init__(model=model)
        # Set the environment variable
        os.environ["GOOGLE_API_KEY"] = api_key
        self.api_key = api_key
        self.model = model
        self.temperature = 0

    def supports_stop_words(self) -> bool:
        return False  # Gemini doesn't support stop words

    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            # Make sure to properly format the model name for litellm
            # litellm expects "google/gemini-1.5-flash" format instead of "gemini/gemini-1.5-flash"
            model = self.model
            if model.startswith("gemini/"):
                model = "google/" + model[7:]  # Convert "gemini/gemini-1.5-flash" to "google/gemini-1.5-flash"
            
            response = completion(
                model=model,
                messages=[{"content": prompt, "role": "user"}],
                temperature=self.temperature,
                max_tokens=500,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            print(f"Error in LLM call: {error_msg}")
            if "API_KEY_INVALID" in error_msg or "INVALID_ARGUMENT" in error_msg:
                return f"❌ ERROR: Invalid API key. Please check your Google API key configuration."
            else:
                return f"❌ ERROR: {error_msg}"