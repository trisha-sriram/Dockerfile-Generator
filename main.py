# main.py

import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# --- Configuration ---
# 1. Load the API key from an environment variable for security.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set. Please set it before running.")

# Configure the Google Generative AI SDK
genai.configure(api_key=GOOGLE_API_KEY)

# --- Pydantic Models ---
# This defines the structure of the incoming request body.
class DockerfileRequest(BaseModel):
    language: str
    package_manager: str
    dependency_file: str
    port: int
    start_command: str
    build_command: Optional[str] = None
    base_image: Optional[str] = None

# --- FastAPI Application ---
app = FastAPI()

# --- Helper Function for Prompt Engineering ---
def create_prompt(request: DockerfileRequest) -> str:
    """Creates a detailed, best-practice prompt for the Gemini model."""

    # Start with the core instruction
    prompt = (
        f"Generate a secure, production-ready, multi-stage Dockerfile for a "
        f"**{request.language}** application using **{request.package_manager}**.\n\n"
        f"**Application Details:**\n"
        f"- The dependency file is named `{request.dependency_file}`.\n"
        f"- The application runs on and exposes port `{request.port}`.\n"
        f"- The command to start the application is `{request.start_command}`.\n"
    )

    # Add optional fields if they were provided
    if request.build_command:
        prompt += f"- The build command is `{request.build_command}`.\n"

    if request.base_image:
        prompt += f"- The user has requested a base image of `{request.base_image}`. Use this if it is a valid and secure choice, otherwise select a suitable slim or alpine official image.\n"

    # Add the best-practice instructions
    prompt += (
        "\n**Instructions & Best Practices to Follow:**\n"
        "- Use multi-stage builds. The first stage should build dependencies, and the final stage should be a lean image with only the production code and necessary dependencies.\n"
        "- Do not run as the `root` user. Create a non-root user (e.g., 'appuser') and switch to it.\n"
        "- Use a `.dockerignore` file (provide an example of what it should contain in a comment).\n"
        "- Leverage Docker layer caching by copying dependency files and installing packages before copying the rest of the source code.\n"
        "- Ensure all permissions are set correctly for the non-root user.\n"
        "- The final output should be only the raw Dockerfile content, without any explanations or markdown formatting like ```dockerfile."
    )
    return prompt

# --- API Endpoints ---
@app.post("/generate")
async def generate_dockerfile(request: DockerfileRequest):
    """
    Receives application details, generates a prompt, calls the Gemini model,
    and returns the generated Dockerfile.
    """
    print("Received request:", request.model_dump())

    try:
        # 2. Create the detailed prompt using our helper function.
        prompt = create_prompt(request)
        print("\n--- Generated Prompt ---\n", prompt)

        # 3. Initialize the Gemini model and generate the content.
        # Use a current, available text model.
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # 4. Extract the text from the response and return it.
        dockerfile_content = getattr(response, "text", None)
        if not dockerfile_content:
            raise RuntimeError("Empty response from model")

        print("\n--- Received AI Response ---\n", dockerfile_content)

        return {"dockerfile": dockerfile_content}

    except Exception as e:
        # Handle potential errors from the API call
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Dockerfile from the AI model.")

@app.get("/")
def read_root():
    return {"message": "Dockerfile Generator API is running!"}
