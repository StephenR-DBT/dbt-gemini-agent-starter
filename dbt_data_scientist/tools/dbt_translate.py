"""dbt warehouse syntax translation tool."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google.genai import Client

# Warehouse-specific syntax patterns for detection
WAREHOUSE_PATTERNS = {
    'snowflake': [
        r'\bIFF\s*\(',  # IFF function
        r'\bFLATTEN\s*\(',  # FLATTEN function
        r'\bLATERAL\s+FLATTEN',  # LATERAL FLATTEN
        r'\bVARIANT\b',  # VARIANT data type
        r'\bQUALIFY\b',  # QUALIFY clause
        r'\$\d+',  # $1, $2 for FLATTEN syntax
        r'::\s*VARIANT',  # ::VARIANT casting
        r'ARRAY_AGG\s*\([^)]*\)\s+WITHIN\s+GROUP',  # Snowflake ARRAY_AGG
    ],
    'bigquery': [
        r'\bSTRUCT\s*\(',  # STRUCT type
        r'\bARRAY\s*\[',  # ARRAY literal syntax
        r'\bUNNEST\s*\(',  # UNNEST function
        r'\bSAFE_CAST\s*\(',  # SAFE_CAST
        r'\bFORMAT_DATE\s*\(',  # FORMAT_DATE
        r'\bPARSE_DATE\s*\(',  # PARSE_DATE
        r'`[^`]+\.[^`]+\.[^`]+`',  # BigQuery table references with backticks
        r'\bGENERATE_UUID\s*\(',  # GENERATE_UUID
    ],
    'redshift': [
        r'\bDISTKEY\b',  # DISTKEY
        r'\bSORTKEY\b',  # SORTKEY
        r'\bCOPY\s+',  # COPY command
        r'\bUNLOAD\s+',  # UNLOAD command
        r'\bLISTAGG\s*\(',  # LISTAGG function
        r'\bDATEADD\s*\(',  # DATEADD function
        r'\bDATEDIFF\s*\(',  # DATEDIFF function
        r'\bGETDATE\s*\(',  # GETDATE function
    ],
    'postgres': [
        r'::\s*\w+',  # :: casting (more specific to postgres)
        r'\bGENERATE_SERIES\s*\(',  # GENERATE_SERIES
        r'\bARRAY_AGG\s*\(',  # ARRAY_AGG
        r'\bSTRING_AGG\s*\(',  # STRING_AGG
        r'\bREGEXP_MATCHES\s*\(',  # REGEXP_MATCHES
        r'\bJSONB\b',  # JSONB data type
        r'\bCROSSTAB\s*\(',  # CROSSTAB
    ]
}

# ------------- Helper: search for files in dbt project -------------
def _search_for_files(dbt_root: str, search_term: str, extensions: List[str] = ['.sql']) -> List[str]:
    """
    Search for files matching the search term in the dbt project.
    
    Args:
        dbt_root: Root directory of the dbt project
        search_term: File name or partial path to search for
        extensions: List of file extensions to search (default: ['.sql'])
    
    Returns:
        List of matching file paths relative to dbt_root
    """
    matches = []
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the DBT_ROOT environment variable, default to current directory
    dbt_path = Path(os.getenv("DBT_PROJECT_LOCATION", os.getcwd()))
    
    # Clean up search term (remove .sql if present for matching)
    search_clean = search_term.lower().replace('.sql', '')
    # Extract just the filename if a path was provided
    search_filename = Path(search_term).name.lower().replace('.sql', '')
    
    # Search through common dbt directories
    search_dirs = ['models', 'macros', 'analyses', 'tests']
    
    for search_dir in search_dirs:
        dir_path = dbt_path / search_dir
        if not dir_path.exists():
            continue
            
        # Recursively search for files
        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                rel_path = file_path.relative_to(dbt_path)
                file_name_clean = file_path.stem.lower()  # filename without extension
                
                # Check if filename matches (exact or contains)
                if search_filename == file_name_clean or search_filename in file_name_clean:
                    matches.append(str(rel_path))
                # Check if search term matches the filename
                elif search_clean == file_name_clean or search_clean in file_name_clean:
                    matches.append(str(rel_path))
                # Also check if the search term appears in the full path
                elif search_clean in str(rel_path).lower():
                    matches.append(str(rel_path))
    
    return sorted(set(matches))

# ------------- Tool: translate dbt SQL between warehouse syntaxes -------------
def dbt_translate(
    file_path: str,
    source_warehouse: str,
    target_warehouse: str
) -> Dict:
    """
    Translate dbt models, macros, or SQL from one warehouse syntax to another.
    
    Args:
        file_path: Path to file relative to dbt project (e.g., 'models/staging/stg_users.sql')
        source_warehouse: Source warehouse type (snowflake, bigquery, redshift, postgres)
        target_warehouse: Target warehouse type (snowflake, bigquery, redshift, postgres)
    
    Returns:
        Dict with status, message, translated_content, and saved_path
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the DBT_PROJECT_LOCATION environment variable, default to current directory
    dbt_project_location = os.getenv("DBT_PROJECT_LOCATION", os.getcwd())
    
    print(f"Translating dbt SQL in: {dbt_project_location}")
    print(f"File: {file_path}")
    print(f"From: {source_warehouse} -> To: {target_warehouse}")
    
    # Resolve source file path
    source_file = Path(dbt_project_location) / file_path
    actual_file_path = file_path  # Track the actual path we're using
    
    # If file doesn't exist, search for similar files
    if not source_file.exists():
        print(f"File not found at exact path: {source_file}")
        print(f"Searching for similar files in project...")
        
        # Search for files matching the search term
        suggestions = _search_for_files(dbt_project_location, file_path)
        
        if not suggestions:
            return {
                "status": "error",
                "message": f"File not found at '{file_path}'. No similar files found in the dbt project. Please provide the full path relative to the dbt project root.",
                "translated_content": None,
                "saved_path": None,
                "suggestions": []
            }
        
        # If there's exactly one match, use it automatically
        if len(suggestions) == 1:
            actual_file_path = suggestions[0]
            source_file = Path(dbt_project_location) / actual_file_path
            print(f"✓ Found matching file: {actual_file_path}")
            print(f"  Using: {source_file}")
        else:
            # Multiple matches found - need user to clarify
            suggestions_list = "\n  - ".join(suggestions[:10])
            return {
                "status": "clarification_needed",
                "message": f"File not found at exact path '{file_path}'. Found {len(suggestions)} possible matches:\n  - {suggestions_list}\n\nPlease specify which file you want to translate using the full path from the list above.",
                "translated_content": None,
                "saved_path": None,
                "suggestions": suggestions[:10],  # Limit to top 10 suggestions
                "original_path": file_path
            }
    else:
        # File found successfully at exact path
        print(f"✓ File found: {source_file}")
    
    # Read source content
    try:
        with open(source_file, 'r') as f:
            source_content = f.read()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading file: {str(e)}",
            "translated_content": None,
            "saved_path": None
        }
    
    # Use Gemini to translate
    try:
        client = Client()
        prompt = f"""Translate this dbt code from {source_warehouse} to {target_warehouse} syntax.
Only return the translated SQL/code, no explanations.

Original code:
{source_content}"""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        translated_content = response.text
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during translation: {str(e)}",
            "translated_content": None,
            "saved_path": None
        }
    
    # Create translated directory structure
    translated_dir = Path(dbt_project_location) / "translated" / target_warehouse
    translated_file = translated_dir / actual_file_path
    translated_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write translated file
    try:
        with open(translated_file, 'w') as f:
            f.write(translated_content)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error writing translated file: {str(e)}",
            "translated_content": translated_content,
            "saved_path": None
        }
    
    return {
        "status": "success",
        "message": f"Successfully translated {actual_file_path} from {source_warehouse} to {target_warehouse}",
        "translated_content": translated_content,
        "saved_path": str(translated_file),
        "source_file": str(source_file),
        "original_path": file_path if file_path != actual_file_path else None
    }

# ------------- Tool: identify files that need translation -------------
def dbt_identify_translation_candidates(
    source_warehouse: str,
    target_warehouse: Optional[str] = None
) -> Dict:
    """
    Scan the dbt project to identify files that likely need translation from one warehouse syntax to another.
    
    Args:
        source_warehouse: Source warehouse type to detect (snowflake, bigquery, redshift, postgres)
        target_warehouse: Optional target warehouse type (for context in the response)
    
    Returns:
        Dict with status, message, and list of files with detected warehouse-specific syntax
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the DBT_PROJECT_LOCATION environment variable, default to current directory
    dbt_project_location = os.getenv("DBT_PROJECT_LOCATION", os.getcwd())
    
    print(f"Scanning dbt project for {source_warehouse} syntax: {dbt_project_location}")
    if target_warehouse:
        print(f"Planning translation to: {target_warehouse}")
    
    # Validate source warehouse
    if source_warehouse.lower() not in WAREHOUSE_PATTERNS:
        return {
            "status": "error",
            "message": f"Unknown source warehouse '{source_warehouse}'. Supported: {', '.join(WAREHOUSE_PATTERNS.keys())}",
            "candidates": []
        }
    
    patterns = WAREHOUSE_PATTERNS[source_warehouse.lower()]
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    # Search through dbt directories
    search_dirs = ['models', 'macros', 'analyses', 'tests']
    dbt_path = Path(dbt_project_location)
    candidates = []
    
    for search_dir in search_dirs:
        dir_path = dbt_path / search_dir
        if not dir_path.exists():
            continue
        
        # Scan all .sql files
        for sql_file in dir_path.rglob('*.sql'):
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for warehouse-specific patterns
                detected_patterns = []
                for i, pattern in enumerate(compiled_patterns):
                    if pattern.search(content):
                        # Get the pattern description from the comment
                        pattern_desc = patterns[i].split('#')[-1].strip() if '#' in str(patterns[i]) else patterns[i]
                        detected_patterns.append(pattern_desc)
                
                if detected_patterns:
                    rel_path = sql_file.relative_to(dbt_path)
                    candidates.append({
                        "file": str(rel_path),
                        "full_path": str(sql_file),
                        "detected_syntax": list(set(detected_patterns)),  # Remove duplicates
                        "pattern_count": len(detected_patterns)
                    })
            
            except Exception as e:
                print(f"Warning: Could not read {sql_file}: {str(e)}")
                continue
    
    # Sort by number of patterns detected (most first)
    candidates.sort(key=lambda x: x['pattern_count'], reverse=True)
    
    if not candidates:
        message = f"No {source_warehouse}-specific syntax detected in the dbt project. Your project may already be warehouse-agnostic or using a different warehouse syntax."
        return {
            "status": "success",
            "message": message,
            "candidates": [],
            "source_warehouse": source_warehouse,
            "target_warehouse": target_warehouse
        }
    
    target_msg = f" to {target_warehouse}" if target_warehouse else ""
    message = f"Found {len(candidates)} file(s) with {source_warehouse}-specific syntax that may need translation{target_msg}."
    
    return {
        "status": "success",
        "message": message,
        "candidates": candidates,
        "total_files": len(candidates),
        "source_warehouse": source_warehouse,
        "target_warehouse": target_warehouse
    }

