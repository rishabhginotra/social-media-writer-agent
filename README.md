# NovaPulse Enterprise Social Media Writer Agent

> **Disclaimer:** This is a personal educational project built for the AI Tech L200 ("AI in 5 Days") capstone assessment and is not an official Google product. All company names (`NovaPulse Cloud Technologies`), products (`PulseGrid`, `PulseShield`, `PulseFlow`), CRM audience segments, and historical social performance metrics in `data/` are fictional synthetic datasets created for demonstration and benchmarking purposes.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![Framework: Google ADK + MCP](https://img.shields.io/badge/Framework-Google_ADK_%2B_MCP-4285F4.svg)](app/agent.py)

---

## 1. Executive Summary & Problem Statement

Writing high-engagement, technically credible social media content at scale is manual and time-consuming. Every post must be customized across **Author Persona**, **Target Audience**, **Platform**, and **Intended Outcome**, while strictly adhering to corporate brand guidelines and grounding claims in real customer and campaign data.

The **NovaPulse Enterprise Social Media Writer Agent** solves this by orchestrating a team of specialized sub-agents powered by **Google ADK**, **Gemini 2.5 Pro / Flash**, and **Model Context Protocol (MCP)** servers:

1. **Parallel MCP Benchmarking & Grounding (`ParallelAgent`)**: Concurrently queries three MCP servers:
   - **CRM Audience & Account Intelligence MCP Server** (`app/mcp_servers/crm_mcp_server.py`): Validated buyer pain points, triggers, and anonymized customer ROI metrics.
   - **Marketing Campaign & Messaging MCP Server** (`app/mcp_servers/marketing_db_mcp_server.py`): Official product value propositions, verified proof points, and outcome-aligned CTAs.
   - **Historic Social Media Performance MCP Server** (`app/mcp_servers/social_performance_mcp_server.py`): Platform-specific engagement/CTR benchmarks, character ranges, and top-performing hook archetypes.
2. **Iterative Brand Compliance Loop (`LoopAgent` + `ComplianceEscalationChecker`)**: Drafts persona-calibrated copy using `gemini-2.5-pro` and validates it via `gemini-2.5-flash` against the **NovaPulse Brand Guidelines v3.2** (`data/brand_guidelines/novapulse_brand_guidelines.md`), automatically remediating any violations until the draft achieves a **Brand Compliance Score $\ge 90/100$** with **0 critical violations**.
3. **Human-in-the-Loop (HITL) Publishing Gatekeeper**: Enforces a pre-execution approval hook (`before_tool_callback`) that pauses live social publication (`pending_human_confirmation`) until a human reviewer explicitly confirms (`human_approval_confirmed=True`).

---

## 2. Architecture & Multi-Agent Workflow

```
User Prompt (Persona + Audience + Platform + Product + Intended Outcome)
   │
   ├──► 1. Pre-Inference Guardrail (ModelArmorGuardrailPlugin.inspect_user_prompt)
   │       • Blocks prompt injection / jailbreaks & scrubs PII via Cloud DLP + regex
   │
   ├──► 2. Context Compaction & Brand Guideline Vector Retrieval (app/context_memory.py)
   │       • Sliding-window token compaction + SQLite vector search over Brand Guidelines
   │
   └──► 3. SocialMediaContentPipeline (SequentialAgent)
           │
           ├──► Stage A: MarketIntelligenceParallelGatherer (ParallelAgent — gemini-2.5-flash)
           │       ├─ CrmAudienceIntelligenceAgent       ──► fetch_crm_audience_segment_insights (MCP)
           │       ├─ MarketingCampaignIntelligenceAgent ──► query_marketing_campaign_value_propositions (MCP)
           │       └─ HistoricSocialBenchmarkAgent       ──► retrieve_historic_social_post_benchmarks (MCP)
           │
           ├──► Stage B: BrandComplianceRefinementLoop (LoopAgent, max_iterations=3)
           │       ├─ PersonaCopywriterAgent (gemini-2.5-pro) ──► Drafts / revises post
           │       ├─ Post-Inference Guardrail                ──► Screens prohibited phrases & PII
           │       ├─ BrandComplianceCriticAgent (flash)      ──► validate_draft_against_brand_guidelines
           │       └─ ComplianceEscalationChecker (BaseAgent) ──► Escalates when score >= 90 & grade == 'pass'
           │
           └──► Stage C: SocialPublishingGatekeeperAgent (HITL Hook — before_tool_callback)
                   └─ publish_approved_social_media_post (Pauses until human_approval_confirmed=True)
                         │
                         └──► Async Background Memory Consolidation (SQLite) + OpenTelemetry Spans & JSON Audit Logs
```

---

## 3. Engineering Excellence Across All 5 Pillars (19 Criteria Mapping)

| Pillar | Criterion | Repository Implementation |
| :--- | :--- | :--- |
| **1. Tool & Interface Design** | **1.1 Comprehensive Tool Docstrings** | `app/tools.py`: Detailed docstrings with `WHEN TO USE`, `WHEN NOT TO USE`, `Args`, and `Returns` on all 5 tools. |
| | **1.2 Descriptive Naming** | `app/tools.py`: `fetch_crm_audience_segment_insights`, `query_marketing_campaign_value_propositions`, `retrieve_historic_social_post_benchmarks`, `validate_draft_against_brand_guidelines`, `publish_approved_social_media_post`. |
| | **1.3 Explicit JSON Schemas** | `app/schemas.py`: 10 strict Pydantic v2 models (`ConfigDict(extra="forbid")`) validating all tool inputs and outputs. |
| | **1.4 Guided Error Handling** | `app/tools.py`: Structured `status="recoverable_error"` payloads with explicit `llm_recovery_instructions` for self-correction. |
| **2. Context & Memory** | **2.1 Robust System Instructions** | `app/prompts.py`: `AGENT_CONSTITUTION_SYSTEM_PROMPT` defining mission, tool protocol, negative constraints, and output format. |
| | **2.2 History Compaction** | `app/context_memory.py` (`TokenBudgetHistoryCompactor`) & `app/agent.py` (`EventsCompactionConfig`). |
| | **2.3 Persistent Session State** | `app/context_memory.py` (`PersistentBrandAndSessionStore`): SQLite session/episodic tables + cosine vector search over Brand Guidelines. |
| | **2.4 Async Memory Operations** | `app/context_memory.py`: `async_consolidate_session_memory` & `schedule_background_consolidation` via `asyncio.create_task`. |
| **3. Orchestration & Logic** | **3.1 Multi-Agent Patterns** | `app/agent.py`: ADK `ParallelAgent`, `LoopAgent` (`ComplianceEscalationChecker`), `SequentialAgent`, and Coordinator `Agent`. |
| | **3.2 Strategic Model Routing** | `app/model_router.py` (`StrategicModelRouter`): Dynamically routes lookups/validation to `gemini-2.5-flash` and synthesis/remediation to `gemini-2.5-pro`. |
| | **3.3 Guardrails & Policy Plugins** | `app/guardrails.py` (`ModelArmorGuardrailPlugin`): Pre-inference injection screen + post-inference brand/PII self-evaluation. |
| | **3.4 Human-in-the-Loop Hooks** | `app/guardrails.py` (`HumanInTheLoopApprovalGate`): `before_tool_callback` pausing live publication until human confirmation. |
| **4. Observability & Tracing** | **4.1 Structured JSON Logging** | `app/observability.py` (`StructuredJsonLogFormatter`, `StructuredAuditLogger`): Cloud Logging JSON schema with trace correlation. |
| | **4.2 Intent vs. Outcome Capture** | `app/observability.py` (`IntentOutcomeAuditTracker`): Explicit `INTENT_DECLARED` (pre-execution) and `OUTCOME_RECORDED` (post-execution) audit trail. |
| | **4.3 Distributed Tracing** | `app/observability.py` (`configure_distributed_tracing`, `start_linked_span`): OpenTelemetry spans across coordinator, MCP servers, and validators. |
| | **4.4 PII Redaction** | `app/observability.py` (`PiiRedactionEngine`): Active regex + Google Cloud DLP (`dlp_v2`) redaction of emails, phones, SSNs, credit cards, and API keys. |
| **5. Infrastructure & CI/CD** | **5.1 Automated Evaluation Suites** | `tests/eval/golden_dataset.json`, `tests/eval/run_evaluation.py`, `tests/eval/eval_config.json`, `tests/eval/evalsets/social_media_writer.evalset.json`. |
| | **5.2 Infrastructure as Code (IaC)** | `deployment/terraform/` (`main.tf`, `variables.tf`, `iam.tf`, `telemetry.tf`, `outputs.tf`) + `.github/workflows/ci-cd.yml` + `[tool.agents-cli]` in `pyproject.toml`. |
| | **5.3 Secure Secret Management** | `app/secret_manager.py` (`SecretManagerClient`) + `deployment/terraform/iam.tf` (`google_secret_manager_secret`). Zero hardcoded keys. |

---

## 4. Repository Structure

```text
social-media-writer-agent/
├── .env.example                                  # Environment & Secret Manager ID template (no raw keys)
├── .github/workflows/ci-cd.yml                   # GitHub Actions CI/CD & Golden Eval Gate (>= 95%)
├── DESIGN_SPEC.md                                # Detailed AgentOps architecture & rubric design spec
├── LICENSE                                       # Apache 2.0 License
├── README.md                                     # Documentation, CLI usage, and deployment guide
├── pyproject.toml                                # Dependencies, pytest config, and [tool.agents-cli]
├── push_to_github.sh                             # One-command push helper for personal GitHub
├── app/
│   ├── __init__.py                               # Exports root_agent and app for ADK CLI
│   ├── agent.py                                  # ParallelAgent, LoopAgent, SequentialAgent & Orchestrator
│   ├── context_memory.py                         # Token sliding window, SQLite state, vector store & async tasks
│   ├── guardrails.py                             # Model Armor pre/post callbacks & HITL approval gate
│   ├── model_router.py                           # Dynamic routing between gemini-2.5-flash & gemini-2.5-pro
│   ├── observability.py                          # Structured JSON logs, Intent/Outcome tracker, OTel & DLP PII redactor
│   ├── prompts.py                                # Agent Constitution & specialized sub-agent prompts
│   ├── schemas.py                                # Strict Pydantic v2 input/output JSON schemas (extra="forbid")
│   ├── secret_manager.py                         # Google Cloud Secret Manager client
│   ├── tools.py                                  # 5 descriptively named tools with guided error recovery
│   └── mcp_servers/                              # Model Context Protocol (MCP) stdio servers
│       ├── __init__.py
│       ├── crm_mcp_server.py                     # CRM Audience & Account Intelligence MCP server
│       ├── marketing_db_mcp_server.py            # Marketing Campaign & Messaging DB MCP server
│       └── social_performance_mcp_server.py      # Historic Social Media Performance Benchmark MCP server
├── data/
│   ├── brand_guidelines/
│   │   └── novapulse_brand_guidelines.md         # Sample company brand guidelines (NovaPulse Cloud Technologies)
│   └── synthetic_db/
│       ├── crm_accounts_and_segments.json        # Synthetic CRM audience segments & anonymized win metrics
│       ├── marketing_campaigns.json              # Synthetic marketing campaigns, proof points & CTAs
│       └── historic_social_performance.json      # Synthetic platform engagement benchmarks & winning hooks
├── deployment/
│   └── terraform/                                # Production GCP Infrastructure as Code
│       ├── main.tf                               # Cloud Run v2, Artifact Registry, GCS & API enablement
│       ├── variables.tf                          # Parameterized project, region, and model variables
│       ├── iam.tf                                # Least-privilege Service Account & Secret Manager bindings
│       ├── telemetry.tf                          # BigQuery audit dataset & Cloud Logging sink
│       └── outputs.tf                            # Exported service URI, SA email, and telemetry dataset ID
└── tests/
    ├── eval/
    │   ├── eval_config.json                      # ADK evaluation threshold configuration
    │   ├── golden_dataset.json                   # Golden multi-persona, multi-platform test cases
    │   ├── run_evaluation.py                     # Automated golden evaluation runner (gate >= 0.95)
    │   └── evalsets/
    │       └── social_media_writer.evalset.json  # ADK CLI evalset specification
    └── unit/
        └── test_rubric_compliance.py             # Unit tests verifying all 19 rubric criteria
```

---

## 5. Quickstart, Testing & Deployment

### 5.1 Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

### 5.2 Run Unit Tests & Automated Golden Evaluation Suite
Both suites run deterministically out-of-the-box:
```bash
# Run the 19-criterion unit test suite
python3 -m unittest discover -s tests/unit -v

# Run the automated Golden Dataset Evaluation Suite (enforces >= 0.95 pass rate)
python3 tests/eval/run_evaluation.py
```

### 5.3 Interactive Local Development with Google ADK & `agents-cli`
```bash
# Launch the interactive ADK Web UI (inspect traces, state, and sub-agent events)
adk web

# Run ADK CLI evaluation against the evalset
adk eval app tests/eval/evalsets/social_media_writer.evalset.json \
  --config_file_path=tests/eval/eval_config.json \
  --print_detailed_results

# Deploy to Cloud Run / Vertex AI Agent Engine using ADK / Agent Starter Pack CLI
adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=us-central1 \
  --service_name=social-media-writer-agent \
  app
```

### 5.4 Provision Production Infrastructure with Terraform
```bash
cd deployment/terraform
terraform init
terraform plan -var="project_id=${GOOGLE_CLOUD_PROJECT}"
terraform apply -var="project_id=${GOOGLE_CLOUD_PROJECT}"
```

### 5.5 One-Command Push to Personal GitHub
```bash
./push_to_github.sh <your-github-username>/<repo-name>
```
