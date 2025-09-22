import os
import json
import subprocess
import pandas as pd
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

load_dotenv()

# ---------------- Tool 1: compile dbt project -----------------
def dbt_compile(_: str = "") -> Dict:
    """
    Runs `dbt compile --log-format json` in DBT_PROJECT_LOCATION
    Returns returncode and logs.
    """
    dbt_project_location = os.getenv("DBT_PROJECT_LOCATION")
    dbt_executable = os.getenv("DBT_EXECUTABLE", "dbt")

    proc = subprocess.run(
        [dbt_executable, "compile", "--log-format", "json"],
        cwd=dbt_project_location,
        text=True,
        capture_output=True
    )
    logs: List[Dict] = []
    for stream in (proc.stdout, proc.stderr):
        for line in stream.splitlines():
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return {
        "returncode": proc.returncode,
        "logs": logs,
        "project_dir": dbt_project_location
    }

# ---------------- Tool 2: analyze compiled dbt project --------
def analyze_dbt_schema(project_dir: Optional[str] = None) -> Dict:
    """
    Looks at compiled dbt SQL files under target/compiled and guesses modeling type.
    """
    project_dir = project_dir or os.getenv("DBT_PROJECT_LOCATION")
    target_dir = os.path.join(project_dir, "target", "compiled")
    patterns = {
        "star_schema": 0,
        "snowflake_schema": 0,
        "data_vault": 0
    }

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".sql"):
                path = os.path.join(root, file)
                sql = open(path).read().lower()
                # naive heuristics:
                if "join" in sql and " on " in sql:
                    patterns["star_schema"] += 1
                if any(tag in sql for tag in ["hub_", "link_", "sat_"]):
                    patterns["data_vault"] += 1
                if any(tag in sql for tag in ["dim_", "fact_"]):
                    patterns["star_schema"] += 1
                if any(tag in sql for tag in ["bridge_", "snowflake_"]):
                    patterns["snowflake_schema"] += 1

    guess = max(patterns, key=patterns.get)
    return {
        "analysis": patterns,
        "likely_modeling_pattern": guess
    }

# ------------- The Agent -------------
dbt_model_analyzer_agent = Agent(
    name="dbt_model_analyzer_agent",
    model="gemini-2.0-flash",
    description="Agent that analyzes the structure of a dbt project and determines the data modeling type.",
    instruction="""
Analyze the dbt project and identify the primary data modeling type used (e.g., star schema, snowflake schema, data vault). 
Provide a brief explanation of the identified data modeling type and any variations or customizations observed in the project.
""",
    tools=[dbt_compile, analyze_dbt_schema]
)
