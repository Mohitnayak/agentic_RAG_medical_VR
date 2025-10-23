<!-- 1b3b90fb-a079-4738-b4b8-d7dccec5d509 40a055e6-154f-449a-96f3-662b645e90c6 -->
# LangChain-Based Agentic Dental VR System

## Architecture Overview

Replace the hardcoded if-else router with a LangChain-based supervisor agent that:

1. Analyzes user questions with LLM
2. Automatically selects the best specialized agent
3. Agents retrieve context from scene_reference.md and RAG
4. Agents use LLM to generate both message and structured JSON
5. All agents share conversation history

## Implementation Steps

### 1. Install Dependencies

Add to `requirements.txt`:

- `langchain==0.1.0`
- `langchain-community==0.0.13`
- `langchain-core==0.1.10`

### 2. Create JSON Schema Files

Create `config/schemas/` directory with individual agent schemas:

**`config/schemas/info_agent.json`**

```json
{
  "type": "answer",
  "agent": "Info Agent",
  "intent": "string",
  "answer": "string",
  "confidence": "float",
  "context_used": "boolean",
  "sources": ["string"]
}
```

**`config/schemas/notes_agent.json`**

```json
{
  "type": "note_action",
  "agent": "Notes Agent",
  "intent": "string",
  "function": "start_notes|add_note|end_notes",
  "message": "string",
  "note_text": "string|null",
  "confidence": "float",
  "context_used": "boolean"
}
```

**`config/schemas/value_agent.json`**

```json
{
  "type": "control_value",
  "agent": "Value Agent",
  "intent": "string",
  "target": "brightness|contrast|opacity",
  "value": "int (0-100)",
  "message": "string",
  "confidence": "float",
  "context_used": "boolean"
}
```

**`config/schemas/control_agent.json`**

```json
{
  "type": "control_on|control_off|control_toggle|implant_select|undo_action|redo_action",
  "agent": "Control Agent",
  "intent": "string",
  "target": "string",
  "value": "string|array|null",
  "message": "string",
  "confidence": "float",
  "context_used": "boolean"
}
```

**Note**: Control Agent `value` field is flexible:

- For toggles: `"on"`, `"off"`, or `null`
- For implants: `["4", "11.5"]` or `"4x11.5"`
- For undo/redo: `null`

### 3. Create Context Loader for scene_reference.md

**`app/scene/context_loader.py`** - New file

- Load and parse scene_reference.md
- Provide methods to retrieve specific sections
- Cache the content for fast access

### 4. Create Base Agent Class

**`app/agent/base_agent.py`** - New file

- Define LangChain agent base class
- Each agent has:
  - Role/personality in system prompt
  - Access to OllamaClient (llama3.1)
  - Context retrieval methods
  - JSON schema loader
  - LLM-based response generator

### 5. Create Specialized Agent Classes

Refactor existing agents to use LangChain:

**`app/agent/info_agent.py`**

- System prompt: "You are an Info Agent that provides dental information..."
- Retrieves context from scene_reference.md AND RAG
- Uses LLM to generate answer
- Formats as JSON using schema

**`app/agent/notes_agent.py`**

- System prompt: "You are a Notes Agent that manages note-taking..."
- Determines note function (start/add/end)
- Uses LLM to extract note text
- Formats as JSON using schema

**`app/agent/value_agent.py`**

- System prompt: "You are a Value Agent that controls image properties..."
- Uses LLM to extract target and value
- Validates range (0-100)
- Formats as JSON using schema

**`app/agent/control_agent.py`**

- System prompt: "You are a Control Agent that manages VR tools..."
- Uses LLM to determine action type, target, and value
- Value can be single (on/off) or array (implant sizes)
- Formats as JSON using schema

### 6. Create LangChain Supervisor Agent

**`app/agent/langchain_supervisor.py`** - New file

- Uses LLM to analyze user question
- Determines which agent should handle it
- Passes conversation history to selected agent
- Returns structured response

System prompt example:

```
You are a Supervisor Agent for a VR Dental Planning system.
Analyze the user's question and determine which agent should handle it:
- Info Agent: Questions about dental anatomy, definitions, locations
- Notes Agent: Recording, documenting, note-taking
- Value Agent: Adjusting brightness, contrast, opacity (0-100)
- Control Agent: Toggling tools, overlays, selecting implants, undo/redo

Return only the agent name: "info", "notes", "value", or "control"
```

### 7. Update Decision Router

**`app/scene/router.py`**

- Replace hardcoded logic with LangChain supervisor call
- Remove all if-else agent selection code
- Remove hardcoded response generation
- Keep conversation history management
- Pass to appropriate LangChain agent

Key changes:

```python
# Old: 300+ lines of if-else
# New: ~50 lines delegating to LangChain agents

def route(self, text, session_id, conversation_history, selected_agent):
    # 1. Pass to supervisor to select agent
    agent_name = supervisor.select_agent(text, conversation_history)
    
    # 2. Get selected agent
    agent = self._get_agent(agent_name)
    
    # 3. Agent retrieves context and generates response
    response = agent.process(text, conversation_history)
    
    return response
```

### 8. Document Alternative Methods

Create `docs/agent_selection_methods.txt`:

- Method B: Multi-agent bidding system
- Method C: Sequential agent routing
- Include pros/cons and implementation notes

### 9. Update Tests

Update existing tests to work with LangChain agents:

- `tests/test_agents.py` - Test each agent's LLM-based processing
- Add tests for context retrieval
- Add tests for JSON schema validation

## Files to Create

- `config/schemas/info_agent.json`
- `config/schemas/notes_agent.json`
- `config/schemas/value_agent.json`
- `config/schemas/control_agent.json`
- `app/scene/context_loader.py`
- `app/agent/base_agent.py`
- `app/agent/langchain_supervisor.py`
- `docs/agent_selection_methods.txt`

## Files to Modify

- `requirements.txt` - Add LangChain dependencies
- `app/agent/info_agent.py` - Convert to LangChain agent
- `app/agent/notes_agent.py` - Convert to LangChain agent
- `app/agent/value_agent.py` - Convert to LangChain agent
- `app/agent/control_agent.py` - Convert to LangChain agent (use flexible value field)
- `app/scene/router.py` - Remove hardcoded logic, use LangChain supervisor
- `tests/test_agents.py` - Update for LangChain agents

## Benefits

- No hardcoded if-else conditions
- LLM-based decision making
- Agents communicate naturally
- Easy to add new agents
- Context-aware responses
- Structured JSON output with flexible value handling
- Maintainable and extensible

### To-dos

- [ ] Add LangChain dependencies to requirements.txt
- [ ] Create JSON schema files for all 4 agents in config/schemas/
- [ ] Create context_loader.py to load and parse scene_reference.md
- [ ] Create base_agent.py with LangChain agent foundation
- [ ] Convert all 4 specialized agents to use LangChain and LLM-based processing
- [ ] Create langchain_supervisor.py for automatic agent selection
- [ ] Refactor router.py to use LangChain supervisor instead of if-else logic
- [ ] Create agent_selection_methods.txt documenting alternative approaches
- [ ] Update tests to work with new LangChain-based agent system