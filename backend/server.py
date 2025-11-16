import os
import json
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import Azure client utilities
from azure_client import get_azure_openai_client, get_azure_deployment_id

# Import local modules
from context import SECURITY_RESEARCHER_INSTRUCTIONS, get_analysis_prompt, enhance_summary
from mcp_servers import create_semgrep_server

# Initialize Azure OpenAI client
client = get_azure_openai_client()
MODEL = "gpt-5-nano"
AZURE_DEPLOYMENT = get_azure_deployment_id(MODEL)

load_dotenv()

app = FastAPI(title="Cybersecurity Analyzer API")

# Configure CORS for development and production
cors_origins = [
    "http://localhost:3000",    # Local development
    "http://frontend:3000",     # Docker development
]

# In production, allow same-origin requests (static files served from same domain)
if os.getenv("ENVIRONMENT") == "production":
    cors_origins.append("*")  # Allow all origins in production since we serve frontend from same domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    code: str


class SecurityIssue(BaseModel):
    title: str = Field(description="Brief title of the security vulnerability")
    description: str = Field(
        description="Detailed description of the security issue and its potential impact"
    )
    code: str = Field(
        description="The specific vulnerable code snippet that demonstrates the issue"
    )
    fix: str = Field(description="Recommended code fix or mitigation strategy")
    cvss_score: float = Field(description="CVSS score from 0.0 to 10.0 representing severity")
    severity: str = Field(description="Severity level: critical, high, medium, or low")


class SecurityReport(BaseModel):
    summary: str = Field(description="Executive summary of the security analysis")
    issues: List[SecurityIssue] = Field(description="List of identified security vulnerabilities")


def validate_request(request: AnalyzeRequest) -> None:
    """Validate the analysis request."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided for analysis")
    
    # Additional validation can be added here
    if len(request.code) > 10000:  # Example: Limit code size
        raise HTTPException(status_code=400, detail="Code exceeds maximum allowed size")


def check_api_keys() -> None:
    """Verify required API keys are configured."""
    required_vars = [
        "AZURE_OPENAI_KEY_GPT_5_NANO",
        "AI_FOUNDRY_ENDPOINT_GPT_5_NANO"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing_vars)}"
        )


async def analyze_with_azure_openai(
    prompt: str,
    semgrep_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze code using Azure OpenAI with the given prompt and optional Semgrep results.
    
    Args:
        prompt: The analysis prompt to send to the model
        semgrep_results: Optional results from Semgrep analysis
        
    Returns:
        Dict containing the analysis results
    """
    # Create the JSON structure as a separate string to avoid f-string formatting issues
    json_structure = """
    {
        "summary": "Brief summary of findings",
        "issues": [
            {
                "title": "Vulnerability title",
                "description": "Detailed description",
                "code": "Vulnerable code snippet",
                "fix": "How to fix the issue",
                "cvss_score": 0.0,
                "severity": "low|medium|high|critical"
            }
        ]
    }
    """
    
    system_message = {
        "role": "system",
        "content": f"""{SECURITY_RESEARCHER_INSTRUCTIONS}

        You MUST return a valid JSON object with the following structure:
        {json_structure}
        """
    }
    
    messages = [
        system_message,
        {"role": "user", "content": prompt}
    ]
    
    if semgrep_results:
        messages.insert(1, {
            "role": "system",
            "content": f"Semgrep analysis results:\n{json.dumps(semgrep_results, indent=2)}"
        })
        print(f"injected S results:\n{json.dumps(semgrep_results, indent=2)}")
    
    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # Parse the response content as JSON
        result = response.choices[0].message.content
        return json.loads(result)
    except json.JSONDecodeError:
        # If the response isn't valid JSON, try to extract a meaningful error
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        return {"error": f"Error calling Azure OpenAI: {str(e)}"}


def run_semgrep_scan(code: str) -> Dict[str, Any]:
    """Run semgrep scan on the provided code and return results."""
    try:
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(code.encode('utf-8'))
        
        # Run semgrep scan
        result = subprocess.run(
            ["semgrep", "--config=auto", "--json", tmp_file_path],
            capture_output=True,
            text=True
        )
        
        # Clean up the temporary file
        try:
            os.unlink(tmp_file_path)
        except Exception:
            pass
            
        if result.returncode != 0 and not result.stdout:
            raise Exception(f"Semgrep scan failed: {result.stderr}")
            
        return json.loads(result.stdout)
    except Exception as e:
        raise Exception(f"Error running semgrep: {str(e)}")


async def run_security_analysis(code: str) -> SecurityReport:
    """
    Execute the security analysis workflow.
    
    Args:
        code: The source code to analyze
        
    Returns:
        SecurityReport: The analysis results
    """
    try:
        print("Starting security analysis...")
        
        # First, run Semgrep analysis
        try:
            print("Initializing Semgrep server...")
            async with create_semgrep_server() as semgrep:
                # TODO: Implement Semgrep analysis and get results
                semgrep_results = {}
                semgrep_results = run_semgrep_scan(code)

                print("Semgrep analysis completed")
        except Exception as semgrep_error:
            print(f"Warning: Semgrep analysis failed: {str(semgrep_error)}")
            semgrep_results = {}
        
        # Prepare the analysis prompt
        try:
            print("Preparing analysis prompt...")
            prompt = get_analysis_prompt(code)
            print(f"Prompt prepared. Length: {len(prompt)} characters")
            
            # Get analysis from Azure OpenAI
            print("Sending request to Azure OpenAI...")
            analysis = await analyze_with_azure_openai(prompt, semgrep_results)
            print("Received response from Azure OpenAI")
            
            if isinstance(analysis, dict) and 'error' in analysis:
                raise ValueError(f"Azure OpenAI API error: {analysis['error']}")
                
            # Convert the analysis to a SecurityReport
            print("Converting response to SecurityReport...")
            print(f"Raw analysis response: {json.dumps(analysis, indent=2)}")
            
            # Ensure the response has the required fields
            if not isinstance(analysis, dict):
                raise ValueError(f"Expected a dictionary response, got {type(analysis).__name__}")
                
            if 'issues' not in analysis:
                raise ValueError("Response is missing required 'issues' field")
                
            # Ensure issues is a list
            if not isinstance(analysis['issues'], list):
                raise ValueError(f"Expected 'issues' to be a list, got {type(analysis['issues']).__name__}")
                
            # Convert each issue to a SecurityIssue
            validated_issues = []
            for i, issue in enumerate(analysis.get('issues', [])):
                try:
                    validated_issues.append(SecurityIssue(**issue))
                except Exception as e:
                    print(f"Warning: Invalid issue at index {i}: {str(e)}")
            
            # Create the final report
            return SecurityReport(
                summary=analysis.get('summary', 'No summary provided'),
                issues=validated_issues
            )
            
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {str(json_err)}")
            raise ValueError("Failed to parse AI response")
            
    except Exception as e:
        # Log the full error with traceback for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in security analysis: {error_trace}")
        
        # Return a more detailed error message
        return SecurityReport(
            summary=f"An error occurred during security analysis: {str(e)}",
            issues=[]
        )


def format_analysis_response(code: str, report: SecurityReport) -> SecurityReport:
    """Format the final analysis response."""
    enhanced_summary = enhance_summary(len(code), report.summary)
    return SecurityReport(summary=enhanced_summary, issues=report.issues)


@app.post("/api/analyze", response_model=SecurityReport)
async def analyze_code(request: AnalyzeRequest) -> SecurityReport:
    """
    Analyze Python code for security vulnerabilities using Azure OpenAI and Semgrep.

    This endpoint combines static analysis via Semgrep with AI-powered security analysis
    to provide comprehensive vulnerability detection and remediation guidance.
    """
    # Validate the request
    validate_request(request)
    check_api_keys()

    try:
        # Run the security analysis
        report = await run_security_analysis(request.code)
        
        # Format the response
        return format_analysis_response(request.code, report)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        print(f"Unexpected error in analyze_code: {str(e)}")
        # Return a generic error message to the client
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis. Please try again later."
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"message": "Cybersecurity Analyzer API"}

@app.get("/network-test")
async def network_test():
    """Test network connectivity to Semgrep API."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://semgrep.dev/api/v1/")
            return {
                "semgrep_api_reachable": True,
                "status_code": response.status_code,
                "response_size": len(response.content)
            }
    except Exception as e:
        return {
            "semgrep_api_reachable": False,
            "error": str(e)
        }

@app.get("/semgrep-test")
async def semgrep_test():
    """Test if semgrep CLI can be installed and run."""
    import subprocess
    import tempfile
    import os
    
    try:
        # Test if we can install semgrep via pip
        result = subprocess.run(
            ["pip", "install", "semgrep"], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "semgrep_install": False,
                "error": f"Install failed: {result.stderr}"
            }
        
        # Test if semgrep --version works
        version_result = subprocess.run(
            ["semgrep", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        return {
            "semgrep_install": True,
            "version_check": version_result.returncode == 0,
            "version_output": version_result.stdout,
            "version_error": version_result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "semgrep_install": False,
            "error": "Timeout during semgrep installation or version check"
        }
    except Exception as e:
        return {
            "semgrep_install": False,
            "error": str(e)
        }

# Mount static files for frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
