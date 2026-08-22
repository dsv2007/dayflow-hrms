# Data Sentinel 🛡️

**Data Sentinel** is an autonomous agent built for the *Build with DataHub: The Agent Hackathon*. 
It acts as a first responder to data pipeline failures, leveraging the **DataHub MCP Server** to diagnose root causes and automatically generate code fixes (like dbt model patches) when upstream schemas change unexpectedly.

## 🏆 Hackathon Challenges Addressed
1. **Agents That Do Real Work:** Data Sentinel automatically investigates data downtime alerts by traversing lineage graphs via DataHub MCP, taking action to resolve the issue.
2. **Metadata-Aware Code Generation:** When a downstream dbt model breaks because an upstream table column was renamed, Data Sentinel reads the exact schema changes from DataHub and generates a working PR to fix the downstream SQL.

## 🚀 How It Works
1. **Trigger:** A mock alert is received (e.g., "dbt test failed on `fct_sales`").
2. **Investigation:** The agent connects to DataHub via MCP and queries the lineage of `fct_sales`.
3. **Diagnosis:** It discovers that the upstream dataset `raw_transactions` recently had a schema change (e.g., column `txn_amount` renamed to `amount`).
4. **Resolution:** The agent rewrites the `fct_sales.sql` dbt model to use the new column name.
5. **Action:** It outputs a ready-to-merge Pull Request with the code fix and a detailed incident report enriched with DataHub metadata.

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10+
- A running DataHub instance (local Docker or Cloud)
- DataHub MCP Server running locally

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/datahub-sentinel.git
   cd datahub-sentinel
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your DataHub credentials or MCP server URL
   ```

### Running the Agent
Run the agent in dry-run mode to see it diagnose an issue and generate a fix:
```bash
python agent.py
```

## 📁 Repository Structure
- `agent.py`: The core LangChain agent logic that reasons about pipeline failures.
- `mcp_client.py`: Helper class to communicate with the DataHub MCP Server.
- `examples/`: Contains sample outputs (generated PRs, fixed SQL code, incident reports) so judges can evaluate the quality of the agent's work without running it.
- `demo_script.md`: The script used for the 3-minute video submission.

## 📜 License
Apache 2.0 (See LICENSE file)
