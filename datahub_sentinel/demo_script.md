# Data Sentinel Demo Script

**Total Time:** ~2 minutes 30 seconds

**[0:00-0:30] Introduction**
*   **Visual:** Show the Devpost project page banner or a slide with the project name "Data Sentinel".
*   **Voiceover:** "Hi everyone! Welcome to Data Sentinel. We've all been there: a critical dashboard breaks, and a data engineer spends hours tracing back through dbt models and Airflow DAGs just to find someone renamed a column in an upstream Postgres table. What if an agent could do that instantly using DataHub?"

**[0:30-1:00] The Problem & The Setup**
*   **Visual:** Show the DataHub UI. Navigate to a dataset (`fct_sales`) and show its lineage back to `raw_transactions`.
*   **Voiceover:** "Here in DataHub, we have a clear lineage graph. But when things break, agents usually lack this context. We built Data Sentinel using the DataHub MCP Server to give an autonomous agent real-time access to this metadata."

**[1:00-1:45] The Action (Terminal & Agent)**
*   **Visual:** Open a terminal. Run `python agent.py`.
*   **Voiceover:** "Let's simulate a pipeline failure alert on `fct_sales`. We kick off Data Sentinel. Watch the terminal. 
    1. First, it connects via MCP and queries the upstream lineage. 
    2. Next, it checks the schema history of upstream datasets. 
    3. Look! It found a schema change on `raw_transactions`—`txn_amount` was renamed to `total_amount`.
    4. Now, it passes this metadata and the broken SQL model to our LLM to generate a fix."

**[1:45-2:15] The Result**
*   **Visual:** Open the generated `examples/incident_report.md` and `examples/fixed_dbt_model.sql` in VS Code.
*   **Voiceover:** "And we're done. Instead of waking up a data engineer, Data Sentinel has drafted a complete incident report enriched with DataHub metadata, and generated the corrected dbt SQL. It replaces the old column name with the new one. This is ready to be merged as a PR."

**[2:15-2:30] Conclusion**
*   **Visual:** Show a final slide with "Data Sentinel - Built with DataHub MCP".
*   **Voiceover:** "By giving agents access to reliable metadata and lineage through DataHub, we move from passive alerts to autonomous resolution. Thank you!"
