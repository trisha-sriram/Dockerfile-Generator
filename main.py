# main.py

import os
import boto3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from botocore.exceptions import ClientError

# --- Configuration ---
# Boto3 will automatically look for AWS credentials in environment variables
# (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).
# Ensure you have enabled model access to 'anthropic.claude-v2:1' in the
# Amazon Bedrock console for your selected region.

# --- Pydantic Models ---
# This defines the structure of the incoming request body.
class DockerfileRequest(BaseModel):
    language: str
    package_manager: str
    dependency_file: str
    port: int
    start_command: str
    build_command: str | None = None
    base_image: str | None  = None

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
    print("Received request:", request.model_dump())

    client = boto3.client("bedrock-runtime", region_name="us-west-2")

    model_id = "anthropic.claude-v2:1"

    prompt = create_prompt(request)
    print("\n--- Generated Prompt ---\n", prompt)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],

    }

    bedrock_rq = json.dumps(native_request)

    try:

        response = client.invoke_model(modelId=model_id, body=bedrock_rq)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

    model_response = json.loads(response["body"].read())

    response_text = model_response["content"][0]["text"]
    print(response_text)

    return {"dockerfile": response_text}

@app.get("/")
def read_root():
    return {"message": "Dockerfile Generator API is running!"}
