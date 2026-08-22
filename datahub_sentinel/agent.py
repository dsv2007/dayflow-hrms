import os
from dotenv import load_dotenv
from mcp_client import DataHubMCPClient
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
# Note: In a real submission, we'd use ChatOpenAI or similar. For demo purposes we mock the LLM output if API key is missing.
from langchain_openai import ChatOpenAI

load_dotenv()

class DataSentinelAgent:
    """
    Data Sentinel: An autonomous agent that investigates data pipeline failures.
    """
    def __init__(self):
        self.mcp = DataHubMCPClient()
        # Initialize LLM if API key is present, otherwise use a mock for the demo
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
            self.use_mock_llm = False
        else:
            print("No OpenAI API key found, running with mock LLM for demo purposes.")
            self.use_mock_llm = True

    def investigate_failure(self, failed_model_urn: str, failed_model_code: str):
        print(f"🚨 ALERT RECEIVED: Pipeline failure detected on {failed_model_urn}")
        
        # Step 1: Trace Lineage via MCP
        print("\n🔍 Step 1: Querying DataHub MCP for upstream lineage...")
        lineage = self.mcp.get_lineage(failed_model_urn)
        upstream_urns = [ent['urn'] for ent in lineage.get('upstreamEntities', [])]
        print(f"Found upstream dependencies: {upstream_urns}")
        
        # Step 2: Check for Schema Changes via MCP
        print("\n🔍 Step 2: Querying DataHub MCP for recent schema changes in upstream datasets...")
        root_cause_urn = None
        schema_changes = None
        
        for urn in upstream_urns:
            metadata = self.mcp.get_schema_metadata(urn)
            history = metadata.get("schemaHistory", [])
            if history:
                print(f"⚠️ SCHEMA CHANGE DETECTED in {urn}:")
                for change in history[0].get("changes", []):
                    print(f"  - {change['type']} on {change['field']}")
                root_cause_urn = urn
                schema_changes = history[0]
                break
                
        if not root_cause_urn:
            print("✅ No upstream schema changes detected. Issue might be elsewhere.")
            return

        # Step 3: Generate Code Fix
        print("\n🛠️ Step 3: Generating code fix via LLM...")
        fixed_code = self._generate_fix(failed_model_code, schema_changes)
        print("✅ Fix generated.")
        
        # Step 4: Output Incident Report
        print("\n📝 Step 4: Generating Incident Report and PR...")
        self._generate_report(failed_model_urn, root_cause_urn, schema_changes, fixed_code)
        
    def _generate_fix(self, broken_code: str, schema_changes: dict) -> str:
        if self.use_mock_llm:
            return broken_code.replace("txn_amount", "total_amount")
            
        prompt = PromptTemplate.from_template(
            "You are a Data Engineer. A dbt model has broken due to an upstream schema change.\n"
            "Upstream changes: {changes}\n"
            "Broken SQL:\n{sql}\n"
            "Please provide the corrected SQL."
        )
        chain = prompt | self.llm
        response = chain.invoke({"changes": schema_changes, "sql": broken_code})
        return response.content

    def _generate_report(self, broken_urn, root_cause_urn, schema_changes, fixed_code):
        report = f"""# 🚨 Incident Report: {broken_urn}
        
## Root Cause Analysis
Data Sentinel automatically traced the lineage of `{broken_urn}` via **DataHub** and discovered a breaking schema change in the upstream dataset `{root_cause_urn}`.

**Changes Detected:**
{schema_changes}

## Proposed Resolution
Data Sentinel has generated the following fix to accommodate the new schema:

```sql
{fixed_code}
```
"""
        os.makedirs("examples", exist_ok=True)
        with open("examples/incident_report.md", "w") as f:
            f.write(report)
        
        with open("examples/fixed_dbt_model.sql", "w") as f:
            f.write(fixed_code)
            
        print("\n🎉 DONE! Incident report and code fix saved to 'examples/' directory.")


if __name__ == "__main__":
    # Mock broken dbt model code
    broken_dbt_sql = \"\"\"
    WITH raw_data AS (
        SELECT * FROM {{ source('production', 'raw_transactions') }}
    )
    SELECT 
        id,
        txn_amount * 0.9 AS discounted_amount
    FROM raw_data
    \"\"\"
    
    agent = DataSentinelAgent()
    agent.investigate_failure(
        failed_model_urn="urn:li:dataset:(urn:li:dataPlatform:dbt,fct_sales,PROD)",
        failed_model_code=broken_dbt_sql
    )
