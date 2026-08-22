from typing import List
from pydantic import BaseModel, Field
import os

class RFPRequirement(BaseModel):
    category: str = Field(description="Category of the requirement (e.g., Security, Timeline, Experience)")
    description: str = Field(description="Description of what is required")

def extract_requirements(rfp_text: str) -> List[RFPRequirement]:
    \"\"\"
    Extracts key requirements from the raw text of an RFP document.
    \"\"\"
    # In a full implementation, we'd use the LLM to parse this out.
    # For demonstration/hackathon purposes, we can use a rule-based or mock approach if needed,
    # but let's assume the agent uses this tool to store extracted findings.
    pass

class Evidence(BaseModel):
    requirement_category: str
    evidence_text: str
    source_document: str

def search_company_knowledge(query: str) -> str:
    \"\"\"
    Searches the company profile and past proposals for evidence related to the query.
    \"\"\"
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
    results = []
    
    # Simple keyword mock search for demonstration
    for root, _, files in os.walk(knowledge_dir):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Return the content if it's broadly relevant (for hackathon demo, we just return all profiles to LLM)
                    results.append(f"Source: {file}\\nContent: {content}\\n---")
                    
    return "\\n".join(results)
