# AI BACK-OFFICE COPILOT — ARCHITECTURE AUDIT

## 1. Executive Summary & Audit Scope
This audit reviews the complete full-stack architecture of **AI Back-Office Copilot**, an enterprise SaaS platform that ingests business datasets (CSV/Excel across Sales, HR, Inventory, Automotive, Operations, and Generic domains), extracts structured **Dataset Knowledge**, executes **deterministic Pandas/DuckDB analytics**, generates **evidence-grounded AI narratives & business analyst chat responses**, and enforces multi-tenant isolation with zero unsupported claims.

---

## 2. Current Architecture Overview

```
                          [ Client: React + Vite + TS ]
                                       │
                         REST API via Axios (/api/v1)
                                       ▼
                       [ FastAPI Backend Application ]
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
  [ Data Ingestion ]          [ Analytics Engine ]            [ AI Services ]
  - Uploads (CSV/XLSX)        - Deterministic Pandas/DuckDB   - Analyst Chat (Multi-turn)
  - Loader & Cleaner          - Query Executor & Planner      - Executive Summary Engine V2
  - Semantic Schema Builder   - Derived Metrics (Profit/HR)   - Multi-Validator Guardrails
  - Capability Detector       - Anomaly & Trend Detectors     - LLM Provider Abstraction
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       ▼
                            [ MongoDB Data Store ]
  - accounts, users, datasets, dataset_knowledge, reports, report_ai_summaries, conversations
```

---

## 3. Detailed Component Inventory

### A. Existing APIs (`backend/app/api/v1/endpoints/`)
| Endpoint Module | Routes / Operations | Current Status & Capabilities |
| :--- | :--- | :--- |
| `uploads.py` | `POST /uploads` | Ingests CSV/Excel up to 25MB, standardizes paths, builds initial schema and capabilities, registers with MongoDB and in-memory registry. |
| `datasets.py` | `GET /datasets`<br>`GET /datasets/{id}`<br>`GET /datasets/{id}/schema`<br>`GET /datasets/{id}/quality`<br>`GET /datasets/{id}/capabilities` | Lists datasets under account; returns schema, data quality stats, and capability lists. Needs explicit `GET /datasets/{id}/knowledge` and `POST /datasets/{id}/refresh-knowledge`. |
| `analyst.py` | `POST /sessions`<br>`GET /sessions/{id}`<br>`POST /sessions/{id}/messages` | Multi-turn conversational Business Analyst. Resolves context, generates deterministic query plans, executes via analytics engine, grounds responses. |
| `analytics.py` | `POST /query`<br>`POST /plan`<br>`GET /capabilities/{id}` | Direct execution of analytics queries and query planning endpoints. |
| `ai.py` | `GET /status`<br>`GET /hardware` | Exposes AI system health, provider information, and hardware acceleration capabilities. |
| `reports.py` | `GET /reports`<br>`GET /reports/{id}`<br>`POST /generate`<br>`POST /{id}/ai-summary`<br>`POST /{id}/ai-summary/regenerate`<br>`GET /{id}/evidence`<br>`POST /{id}/generate-pdf`<br>`GET /{id}/pdf` | Report generation, catalog retrieval, dynamic V2 AI Executive Summary with cache invalidation, and ReportLab PDF compilation. |
| `mappings.py` | Mapping configurations | Schema column overrides and semantic mappings. |
| `dashboard.py`| Dashboard overview | Aggregates KPIs across uploaded datasets for tenant. |
| `auth.py` | JWT authentication | User registration, login, token refresh, and tenant binding. |

### B. Existing Database Architecture (`backend/app/db/`)
- **Engine**: MongoDB with Motor / PyMongo driver (`database.py`, `mongodb.py`).
- **Repositories**:
  - `account_repository.py`: Tenant / Account metadata and settings.
  - `user_repository.py`: User credentials, roles, and account association.
  - `dataset_repository.py`: Dataset metadata, file paths, row/col counts, profiles.
  - `knowledge_repository.py`: Stores dataset knowledge structures.
  - `report_repository.py`: Stores generated reports, report versions, and V2 AI summaries with filter hashes.
  - `conversation_repository.py`: Persists multi-turn chat sessions and message logs.
  - `schema_repository.py`: Persists semantic column mappings.
- **Tenant Isolation**: Account-level scoping is implemented on key collections (`account_id`), but requires standardized `tenant_id` enforcement and index coverage across all 14 required collections.

### C. Existing AI & Analyst Implementation (`backend/app/ai/`, `backend/app/analyst/`)
- **Analyst Pipeline**:
  - `intent_classifier.py`: Maps inquiries to `COUNT`, `COUNT_UNIQUE`, `SUM`, `AVERAGE`, `TOP_ENTITY`, `BOTTOM_ENTITY`, `DERIVED_METRIC`, `LIST_UNIQUE`, `QUALITY`.
  - `query_planner.py`: Translates questions to structured `QueryPlan` instances without performing premature arithmetic.
  - `context_manager.py` & `conversation_context.py`: Resolves conversational references (e.g. "its quantity", "them") across turns.
  - `dataset_resolver.py`: Resolves target dataset when user asks questions without explicit dataset qualification.
  - `answer_builder.py`: Formats deterministic answers into natural business text.
  - `llm_service.py` & `llm_provider.py`: Communicates with LLM API (Groq/OpenAI/Gemini) with deterministic fallback on failure.

### D. Existing Summary Engine & Evidence Builder (`backend/app/reporting/`)
- **Universal 45-Rule System Prompt**: Active in `executive_summary.py`.
- **Two-Stage Architecture**:
  - Stage A (`ai_evidence_planner.py`): Selects direct evidence, omits irrelevant metrics, evaluates meaningful comparisons/trends.
  - Stage B (`executive_summary.py`): Synthesizes natural executive narrative strictly bound to approved planner evidence.
- **Evidence Builder (`report_evidence_builder.py`)**: Produces stable dot-notation IDs (`metric.*`, `ranking.*`, `quality.*`, `comparison.*`, `trend.*`) with semantic metadata (`semantic_measure`, `aggregation`, `unit`, `currency`, `scope`, `source`).
- **Grounding & Guardrails**:
  - `report_relevance.py`: Domain relevance isolation (HR vs Sales vs Data Quality vs Profitability).
  - `semantic_validator.py`: Measure alignment (e.g., revenue is never called "volume").
  - `benchmark_validator.py`: Categorizes benchmarks (`OBSERVED`, `INTERNAL`, `EXTERNAL`, `NO_BENCHMARK`).
  - `risk_claim_validator.py`: Rejects ungrounded "talent loss" or "financial risk" labels.
  - `trend_validator.py`: Prohibits temporal assertions without calculated chronological analytics.
  - `comparison_validator.py`: Sentence-scoped comparison checks preventing inverted top/bottom rankings.
  - `recommendation_validator.py`: Requires evidence IDs for all action points; bans generic filler.
  - `duplicate_claim_detector.py`: Eliminates cross-section repetition.
  - `claim_grounding_validator.py`: Number/percentage tolerance verification.

---

## 4. Reusable Components & Strong Foundations
1. **Analytics Engine (`app/analytics/engine.py`)**: Robust deterministic computation engine for tabular data with DuckDB and Pandas.
2. **Acceptance Test Suites (`tests/test_mandatory_acceptance.py`, `tests/ai_summary/`, `tests/reporting/`)**: 100% passing test suites covering 214+ automated scenarios.
3. **Frontend Dynamic UI (`DynamicExecutiveSummary.tsx`, `UniversalReportRenderer.tsx`)**: Responsive, data-driven report rendering with truthful badges (`AI_GENERATED_GROUNDED`, `VERIFIED_ANALYTICS_ONLY`).
4. **ReportLab PDF Generator (`app/reporting/pdf_generator.py`)**: Professional multi-page PDF rendering engine that respects verified analytics.

---

## 5. Identified Gaps & Architectural Conflicts

### Gap 1: Modular Package Structure for AI Dataset Profiling (Section 5)
- **Current State**: Profiling and semantic detection logic are scattered across `app/data/profiler.py`, `app/data/semantic/`, and `app/data/knowledge/`.
- **Requirement**: Section 5 explicitly specifies `backend/app/ai/dataset/`:
  - `profiler.py`, `semantic_mapper.py`, `domain_detector.py`, `entity_detector.py`, `synonym_detector.py`, `capability_detector.py`, `relationship_detector.py`, `knowledge_builder.py`, `knowledge_repository.py`.
- **Action**: Create `backend/app/ai/dataset/` providing the complete NLP profiler, entity/synonym detection, and rich `DatasetKnowledge` object matching Section 4, while maintaining backward-compatible aliases for existing imports.

### Gap 2: Unified LLM Provider Abstraction with Hugging Face (Section 10 & 11)
- **Current State**: `app/ai/llm_provider.py` and `app/ai/provider.py` handle cloud providers (Groq, OpenAI, Gemini) directly without a formal provider factory or optional HuggingFace provider.
- **Requirement**: Section 10 specifies `backend/app/ai/providers/`:
  - `base.py`, `cloud.py`, `huggingface.py`, `factory.py`, `models.py`.
  - Configurable via `LLM_PROVIDER=cloud` or `LLM_PROVIDER=huggingface`.
  - Hugging Face must be completely optional (gracefully falls back if `transformers`/`torch` are absent), and MUST NOT fine-tune customer private data into global weights.
- **Action**: Implement `backend/app/ai/providers/` with `BaseLLMProvider`, `CloudLLMProvider`, `HuggingFaceProvider`, and `LLMProviderFactory`.

### Gap 3: Canonical Validation Layer Unification (Section 31)
- **Current State**: Validators currently live in `backend/app/reporting/` (for summaries) and `backend/app/ai/` / `backend/app/validation/` (for chat).
- **Requirement**: Section 31 specifies `backend/app/ai/validation/`:
  - `claim_extractor.py`, `claim_grounding_validator.py`, `semantic_validator.py`, `number_validator.py`, `benchmark_validator.py`, `risk_claim_validator.py`, `trend_validator.py`, `comparison_validator.py`, `recommendation_validator.py`, `duplicate_claim_detector.py`, `unsupported_inference_validator.py`.
- **Action**: Consolidate and re-export the unified validation pipeline under `backend/app/ai/validation/` so both AI Analyst chat and AI Summary engine execute the identical 12-point guardrail sequence.

### Gap 4: Dataset Knowledge Endpoints & Multi-Dataset Disambiguation (Section 17 & 39)
- **Current State**: `GET /api/v1/datasets/{id}/knowledge` and `POST /api/v1/datasets/{id}/refresh-knowledge` are missing from `datasets.py`. Chat dataset disambiguation needs explicit multi-dataset prompts when questions match multiple loaded files.
- **Action**: Add dedicated knowledge endpoints to `datasets.py` and implement interactive disambiguation in `dataset_resolver.py`.

### Gap 5: Multi-Tenant MongoDB Collection Coverage (Section 9)
- **Current State**: MongoDB collections exist for datasets, reports, accounts, users, and conversations.
- **Requirement**: Explicit tracking of all 14 collections with `tenant_id` and `account_id` isolation:
  - `accounts`, `users`, `datasets`, `dataset_versions`, `dataset_knowledge`, `analytics_results`, `reports`, `report_versions`, `report_evidence`, `ai_summaries`, `ai_conversations`, `ai_messages`, `ai_validation_logs`, `ai_generation_logs`.
- **Action**: Update `indexes.py` and database helpers to guarantee indexes on `(tenant_id, account_id)` across all collections.

---

## 6. Migration & Refactoring Plan

```
Phase 1: Knowledge & Profiler Architecture (app/ai/dataset/)
Phase 2: LLM Provider Abstraction & Hugging Face Layer (app/ai/providers/)
Phase 3: Canonical Validation Stack (app/ai/validation/)
Phase 4: Multi-Tenant Database & Collection Normalization
Phase 5: API Endpoints & Multi-Dataset Disambiguation
Phase 6: Frontend Integration & Knowledge Status UI
Phase 7: End-to-End Verification & 12 Acceptance Tests
```
