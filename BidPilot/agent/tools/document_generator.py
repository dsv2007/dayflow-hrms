def generate_final_document(draft: str, output_path: str = "documents/final_proposal.pdf"):
    \"\"\"
    Converts the final, user-approved draft into a formatted PDF or Docx for submission.
    \"\"\"
    # Mocking for hackathon demo
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(draft)
    return output_path
