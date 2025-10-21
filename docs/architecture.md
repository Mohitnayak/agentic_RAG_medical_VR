### System Architecture

This document provides a high-level block diagram and component overview of the intelligent, config-driven agentic RAG system for VR dental surgical planning.

#### Block Diagram

```mermaid
flowchart TB
    UI[Web UI / HTTP Client] --> API[Flask API /api/v1/chat]

    subgraph Config[Configuration Layer (config/*.json)]
        INTENT_CFG[intent.json\n- verbs, thresholds, classifier]
        ENTITIES_CFG[entities.json\n- scene elements, synonyms, locations]
        RANGES_CFG[ranges.json\n- numeric ranges, implant limits]
        RETRIEVAL_CFG[retrieval.json\n- hybrid weights, top-k]
    end

    API --> ROUTER[DecisionRouter]
    Config --> ROUTER

    ROUTER --> IC[Intent Classifier\n(rule-based ML)]
    ROUTER --> ER[Entity Resolver\n(semantic + lexical)]
    ROUTER --> NP[Numeric Parser\n(Recognizers-Text)]

    IC --> CONF[Confidence Aggregation]
    ER --> CONF
    NP --> CONF

    CONF --> DECIDE{confidence ≥ router_cutoff?}
    DECIDE -->|yes| ACTIONS[Route to Action]
    DECIDE -->|no| CLARIFY[Targeted Clarification]

    ACTIONS --> CTRL[Tool Action\n{"tool":"control", args}]
    ACTIONS --> INFO[Info Answer\n(definition/location)]
    ACTIONS --> SIZE[Size Request Flow\n(implants)]

    CTRL --> VALID[Pydantic Validation]
    INFO --> VALID
    SIZE --> VALID
    VALID --> RESP[Structured Response]
    RESP --> API

    %% Validation failure → fallback RAG
    API -->|validation error| RAG[RAG Fallback]
    RAG --> RET[Retriever\n(hybrid fusion)]
    RET --> LEX[Lexical scorer]
    RET --> EMB[Embeddings (Ollama)]
    RET --> VS[FAISS Vector Store]
    VS --> DB[(SQLite: documents, chunks)]
    RET --> AGENT[Agent Planner]
    AGENT --> LLM[Ollama Llama 3.1]
```

#### Components Overview

- Intent Classification (app/scene/classifier.py)
  - Rule-based ML classifier; configurable via `config/intent.json`
  - Labels: control_on/off/value, info_definition, info_location, size_request

- Entity Resolution (app/scene/entity_resolver.py)
  - Semantic (embeddings) + lexical overlap against `config/entities.json`
  - Returns best-matching canonical entity + confidence

- Numeric Parsing (app/scene/values.py)
  - Uses Microsoft Recognizers-Text style parsing for values and implant sizes
  - Validates ranges against `config/ranges.json`

- Decision Router (app/scene/router.py)
  - Orchestrates intent/entity/value with thresholds from `config/intent.json`
  - Low confidence → clarifications; high confidence → tool/info routes

- Tools (app/tools/*)
  - `control` tool validates targets and values using `config/entities.json` and `config/ranges.json`
  - Pydantic schemas enforce structured outputs

- RAG (app/rag/*)
  - Hybrid retrieval (semantic + lexical) with weights from `config/retrieval.json`
  - FAISS vector store + SQLite-backed metadata; Ollama embeddings

- API (app/routes.py)
  - `/api/v1/chat` → DecisionRouter → validation → response or RAG fallback
  - `/api/v1/ingest` → document ingestion and chunking

- Config Loader (app/config_loader.py)
  - Centralized loader for all JSON configs under `config/`

#### Typical Request Flow

1) User sends input to `/api/v1/chat`.
2) DecisionRouter classifies intent, resolves entities, parses values.
3) Confidence combined; if below cutoff → clarification.
4) Otherwise, route to tool action or info response; validate with Pydantic.
5) If validation fails, fallback to RAG: retrieve context and answer with agent.
6) Return structured JSON to the client.

#### Key Guarantees

- Config-driven behavior (verbs, entities, ranges, weights) without code changes.
- Deterministic structured outputs; invalid requests trigger clarifications.
- Domain-bounded responses; out-of-domain queries avoid hallucinations.


