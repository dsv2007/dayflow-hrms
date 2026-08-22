def generate_proposal_draft(compliance_data: dict) -> str:
    \"\"\"
    Generates a draft of the proposal using the satisfied evidence.
    \"\"\"
    draft = "## Proposal Draft\\n\\n"
    for req in compliance_data:
        draft += f"### {req['requirement']}\\n"
        if req['status'] == "SATISFIED":
            draft += f"{req['evidence']}\\n\\n"
        else:
            draft += f"*[⚠️ WARNING: Missing Information. Action Required]*\\n\\n"
    return draft
