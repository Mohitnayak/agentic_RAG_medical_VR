# Agentic RAG (Flask + Ollama Llama 3.1)

A local-first, text-only agentic RAG system focused on dental surgical planning (extensible to other domains). Uses Flask, FAISS, and Ollama (Llama 3.1 + nomic-embed-text).

## Prerequisites
- Anaconda/Miniconda
- Windows 10/11
- (Recommended) Ollama for Windows to run local models

## Quick Start (Windows)

### 1) Create and activate env
```bash
conda create -y -n medallion_agents python=3.11
conda activate medallion_agents
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
```

### 2) Install Ollama (models)
- Install Ollama for Windows: see `https://ollama.com/download`
- Pull models:
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```
- Start Ollama service (if not auto-started):
```bash
ollama serve
```

### 3) Initialize database
```bash
flask --app manage.py init-db
```

### 4) Ingest content
- Option A (raw text):
```bash
flask --app manage.py ingest-text --text "Dental implant planning basics..." --title "Guide" --domain dental
```
- Option B (text file):
```bash
flask --app manage.py ingest-text --file path\\to\\doc.txt --title "My Doc" --domain dental
```

### 5) Run the app
```bash
python manage.py
```
Open `http://localhost:5000` in your browser.

### Architecture

See `docs/architecture.md` for a block diagram and component overview.

## API Endpoints (v1)
- POST `/api/v1/ingest` → index documents
- POST `/api/v1/chat` → RAG chat with tool/notes-aware agent
- POST `/api/v1/notes/start` → begin note-taking
- POST `/api/v1/notes/add` → add note line
- POST `/api/v1/notes/end` → finalize notes
- GET `/api/v1/notes/{sessionId}` → list notes

## Configuration

### Environment Variables (Optional)
- `OLLAMA_HOST` (default `http://localhost:11434`)
- `DB_URL` (default `sqlite:///rag.db`)
- `VECTOR_STORE` (`faiss` default)
- `CHAT_MODEL` (`llama3.1` default)
- `EMBEDDING_MODEL` (`nomic-embed-text` default)

### Configuration Files

The system uses JSON configuration files under `config/` for intelligent intent handling:

#### `config/intent.json` - Intent Classification
```json
{
  "verbs": {
    "on": ["turn on", "enable", "switch on", "start", "show", "give me"],
    "off": ["turn off", "disable", "switch off", "stop", "hide"],
    "info": ["what is", "what are", "definition of", "tell me about"],
    "location": ["where is", "where are", "which side"]
  },
  "thresholds": {
    "intent_confidence": 0.6,
    "entity_confidence": 0.5,
    "value_confidence": 0.4,
    "router_cutoff": 0.3
  },
  "classifier": {
    "enabled": false,
    "model": "facebook/bart-large-mnli",
    "labels": ["control_on", "control_off", "control_value", "info_definition", "info_location", "size_request", "none"]
  }
}
```

#### `config/ranges.json` - Value Validation
```json
{
  "contrast": { "min": 0, "max": 100 },
  "brightness": { "min": 0, "max": 100 },
  "implants": {
    "height_y_mm": { "min": 3.0, "max": 4.8 },
    "length_z_mm": { "min": 6.0, "max": 17.0 }
  }
}
```

#### `config/retrieval.json` - Hybrid Search
```json
{
  "hybrid_weights": {
    "semantic": 0.7,
    "lexical": 0.3
  },
  "top_k": {
    "semantic": 10,
    "lexical": 5,
    "final": 8
  }
}
```

#### `config/entities.json` - Scene Elements
```json
{
  "entities": [
    {
      "name": "handles",
      "type": "switch",
      "location": "right side menu bar",
      "definition": "Interactive controls for manipulating scene elements",
      "synonyms": ["handle", "controls", "buttons"]
    }
  ]
}
```

### Enabling Advanced Features

#### Zero-Shot Intent Classifier
To enable the HF zero-shot classifier for better intent recognition:

1. Install transformers: `pip install transformers torch`
2. Set `"enabled": true` in `config/intent.json`
3. Restart the application

#### Semantic Entity Resolution
For better entity recognition using embeddings:

1. Install sentence-transformers: `pip install sentence-transformers`
2. The system will automatically use semantic resolution with lexical fallback

### Extending Without Code Changes

#### Adding New Verbs
Edit `config/intent.json` → `verbs` section:
```json
"custom_action": ["do something", "perform task", "execute command"]
```

#### Adding New Entities
Edit `config/entities.json` → `entities` array:
```json
{
  "name": "new_element",
  "type": "switch",
  "location": "left side",
  "definition": "Description of the element",
  "synonyms": ["alias1", "alias2"]
}
```

#### Adjusting Confidence Thresholds
Edit `config/intent.json` → `thresholds` section to fine-tune when clarifications are requested.

### Example Interactions

| Input | Response Type | Example Output |
|-------|---------------|----------------|
| "turn on handles" | Tool Action | `{"tool": "control", "arguments": {"hand": "right", "target": "handles", "operation": "set", "value": "on"}}` |
| "what are implants" | Answer | `{"type": "answer", "answer": "Dental implants are...", "context_used": false}` |
| "where is the skull" | Answer | `{"type": "answer", "answer": "The skull model is on the left side", "context_used": false}` |
| "set brightness 50%" | Tool Action | `{"tool": "control", "arguments": {"hand": "right", "target": "brightness", "operation": "set", "value": 50}}` |
| "do something" | Clarification | `{"type": "clarification", "message": "I need more information:", "clarifications": ["Could you clarify what you'd like to do?"]}` |

## Notes & Tooling
- Notes: start/end APIs manage session-scoped notes. When active, the agent encourages note entry.
- Tools: initial `activate_tool` allows structured activation with arbitrary properties.

## Safety
- The assistant provides educational guidance; avoid diagnosis and defer to clinicians.

## Testing & Evaluation

### Running Tests
```bash
pytest -q
```

### Evaluation Fixtures
Run the evaluation fixtures to test the intelligent intent handling:
```bash
python tests/eval_fixtures.py
```

This will test various scenarios:
- Control actions ("turn on handles", "set brightness 50%")
- Information requests ("what are implants", "where is the skull")
- Size requests ("implant size 4 x 11.5")
- Clarification cases ("do something", "turn on")

### Confidence Logging
The system logs low-confidence cases and clarifications to `logs/confidence.log` for analysis and improvement.

### Performance Monitoring
Monitor the logs to:
- Identify frequently unclear inputs
- Adjust confidence thresholds
- Add missing synonyms or entities

## Roadmap
- Add Qdrant vector store option
- Reranking and hybrid retrieval
- Auth, RBAC, observability
- Voice note-taking

