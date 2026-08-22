from pydantic import BaseModel, Field

class Requirement(BaseModel):
    id: str
    description: str
    category: str

def extract_specific_requirements(rfp_text: str) -> list[Requirement]:
    \"\"\"
    Takes raw RFP text and extracts discrete requirements that need evidence backing.
    \"\"\"
    # Mocked for hackathon
    return [
        Requirement(id="req-1", description="5+ years experience", category="Experience"),
        Requirement(id="req-2", description="ISO 27001 certification", category="Security")
    ]
