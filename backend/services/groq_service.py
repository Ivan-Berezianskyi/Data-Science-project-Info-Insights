from groq import Groq
import os

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY", ""),
)