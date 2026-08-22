def check_compliance(requirements: list, evidence: dict) -> dict:
    \"\"\"
    Cross-references requirements against found evidence to calculate a compliance score.
    Flags missing evidence for user review.
    \"\"\"
    results = {
        "score": 0,
        "missing": []
    }
    
    total = len(requirements)
    if total == 0:
        return results
        
    met = 0
    for req in requirements:
        cat = req.category
        if cat in evidence and "None found" not in evidence[cat]:
            met += 1
        else:
            results["missing"].append(req.description)
            
    results["score"] = int((met / total) * 100)
    return results
