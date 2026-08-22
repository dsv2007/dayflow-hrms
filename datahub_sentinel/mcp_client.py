import os
import requests
import json
from typing import Dict, Any, List

class DataHubMCPClient:
    """
    A client to interact with the DataHub Model Context Protocol (MCP) Server.
    For the hackathon demo, if the MCP server isn't available, it falls back to 
    simulated responses to demonstrate the agent's logic.
    """
    
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or os.getenv("DATAHUB_MCP_SERVER_URL", "http://localhost:8080/mcp")
        self.token = token or os.getenv("DATAHUB_PERSONAL_ACCESS_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Flag for demo mode (if the real server isn't running)
        self.demo_mode = True

    def get_lineage(self, urn: str, direction: str = "UPSTREAM") -> Dict[str, Any]:
        """
        Retrieves the lineage for a given entity URN.
        """
        if self.demo_mode:
            # Simulated lineage response showing fct_sales depends on raw_transactions
            if "fct_sales" in urn:
                return {
                    "urn": urn,
                    "upstreamEntities": [
                        {
                            "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_transactions,PROD)",
                            "type": "dataset"
                        }
                    ]
                }
            return {"urn": urn, "upstreamEntities": []}
            
        # Real MCP Server call
        payload = {
            "jsonrpc": "2.0",
            "method": "get_lineage",
            "params": {"urn": urn, "direction": direction},
            "id": 1
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json().get("result", {})

    def get_schema_metadata(self, urn: str) -> Dict[str, Any]:
        """
        Retrieves the latest schema metadata and schema history for a dataset.
        """
        if self.demo_mode:
            # Simulated response showing a recent schema change
            if "raw_transactions" in urn:
                return {
                    "urn": urn,
                    "schemaMetadata": {
                        "fields": [
                            {"fieldPath": "id", "type": "string"},
                            {"fieldPath": "total_amount", "type": "number", "description": "Renamed from txn_amount"}
                        ]
                    },
                    "schemaHistory": [
                        {
                            "timestamp": "2026-08-10T10:00:00Z",
                            "changes": [
                                {"type": "DROP_COLUMN", "field": "txn_amount"},
                                {"type": "ADD_COLUMN", "field": "total_amount"}
                            ]
                        }
                    ]
                }
            return {"urn": urn, "schemaMetadata": {}}
            
        payload = {
            "jsonrpc": "2.0",
            "method": "get_schema",
            "params": {"urn": urn},
            "id": 2
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json().get("result", {})
