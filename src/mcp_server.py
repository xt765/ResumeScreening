"""MCP Server for Resume Screening.

Provides MCP tools for screening resumes and searching talents.
"""
import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from loguru import logger

from src.core.logger import setup_logger
from src.workflows.resume_workflow import run_resume_workflow

# Initialize logger
setup_logger()

# Create an MCP server
mcp = FastMCP("ResumeScreening")

@mcp.tool()
async def screen_resume(file_path: str, filter_config_json: str) -> str:
    """Screen a resume using complex filter configuration.

    Args:
        file_path: Absolute path to the resume file (PDF/DOCX).
        filter_config_json: JSON string containing the filter configuration.
            Example: {"groups": [{"logic": "and", "condition_ids": ["id1"]}], "group_logic": "and"}
            Or simplified: {"skills": ["Python"], "education_level": "master"} (if supported by workflow)

    Returns:
        JSON string containing the screening result (is_qualified, score, reason, etc.).
    """
    try:
        logger.info(f"MCP Tool Request: screen_resume file={file_path}")
        try:
            config = json.loads(filter_config_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for filter_config"}, ensure_ascii=False)

        # Execute workflow
        result = await run_resume_workflow(file_path=file_path, filter_config=config)
        
        # Convert result to JSON string (handle datetime etc via default=str)
        return json.dumps(result, ensure_ascii=False, default=str)
    
    except Exception as e:
        logger.error(f"MCP Tool Error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def check_health() -> str:
    """Check if the Resume Screening service is healthy."""
    return "Resume Screening Service is running."

if __name__ == "__main__":
    mcp.run()
