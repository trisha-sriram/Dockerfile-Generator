from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

class DockerfileRequest(BaseModel):
    language: str
    package_manager: str
    dependency_file: str
    port: int
    start_command: str
    build_command: Optional[str] = None
    base_image: Optional[str] = None

app = FastAPI()

@app.post("/generate")
async def generate_dockerfile(request: DockerfileRequest):
    print("Received request:", request.model_dump())
    
    mock_dockerfile = """
# Stage 1: Build dependencies
FROM python:3.13-slim-bullseye AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Create final production image
FROM python:3.13-slim-bullseye
WORKDIR /app
COPY --from=builder /app /app
EXPOSE 8000
CMD ["python", "app.py"]
"""
    return {"dockerfile": mock_dockerfile}

@app.get("/")
def read_root():
    return {"message": "Dockerfile Generator API is running!"}

