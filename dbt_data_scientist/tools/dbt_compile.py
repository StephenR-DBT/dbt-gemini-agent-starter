"""dbt local compile tool with fusion."""

import os, json, subprocess
from typing import Dict, List
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools import FunctionTool
# ------------- Tool: run `dbt compile` and return JSON logs -------------
def dbt_compile(compile: str) -> str:
    """
    Runs `dbt compile --log-format json` in the DBT_ROOT and returns:
    returncode
    logs: list of compiled JSON events (dbt emits JSON per line)
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the DBT_ROOT environment variable, default to current directory
    dbt_project_location = os.getenv("DBT_PROJECT_LOCATION", os.getcwd())
    dbt_executable = os.getenv("DBT_EXECUTABLE")
    
    print(f"Running dbt compile in: {dbt_project_location}")
    print(f"Running dbt executable located here: {dbt_executable}")

    proc = subprocess.run(
            [dbt_executable, "compile", "--log-format", "json"],
            cwd=dbt_project_location,
            text=True,
            capture_output=True
        )
    print(proc)
    logs: List[Dict] = []
    for stream in (proc.stdout, proc.stderr):
        for line in stream.splitlines():
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                # ignore non-JSON lines quietly
                pass
    return {"returncode": proc.returncode, "logs": logs}