# BidPilot: Evidence-Grounded RFP Response & Compliance Agent

BidPilot is an evidence-grounded AI agent that autonomously analyzes RFPs, maps requirements to organizational evidence, generates tailored responses, identifies unsupported claims, asks for missing information, performs compliance auditing, and produces a submission-ready proposal.

## Tech Stack
* **Language**: Python
* **Agent Framework**: Strands Agents SDK
* **LLM**: Amazon Bedrock – Claude Sonnet 4.6
* **Agent Runtime**: Amazon Bedrock AgentCore Runtime (optional deployment target)
* **UI**: Streamlit
* **Knowledge Retrieval**: Document ingestion + embeddings/vector search over company documents, previous proposals, case studies, and certifications.

## Setup Instructions

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```
3. **Configure Environment Variables**
   Copy `.env.example` to `.env` and fill in your AWS credentials or other API keys.
   ```bash
   cp .env.example .env
   ```
4. **Run the App**
   ```bash
   uv run streamlit run app/main.py
   ```

## Architecture

Please see the `architecture/` folder for the architecture diagram.
