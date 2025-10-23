# Medallion Agents: Multi-Agent VR Dental Planning System

## Executive Summary

The Medallion Agents system is a sophisticated multi-agent architecture designed for Virtual Reality (VR) dental planning applications. The system employs a hybrid approach combining Large Language Model (LLM) supervision with specialized domain agents to provide intelligent, context-aware assistance in dental implant planning scenarios.

## System Architecture Overview

### 1. Core Architecture Pattern

The system follows a **Supervisor-Agent Pattern** with the following key components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │◄──►│   Flask API      │◄──►│  Agent Router    │
│   (HTML/JS)     │    │   (REST API)     │    │  (Decision      │
└─────────────────┘    └──────────────────┘    │   Router)        │
                                               └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │ LangChain       │
                                               │ Supervisor      │
                                               └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │ Specialized     │
                                               │ Agents          │
                                               │ (Info/Notes/    │
                                               │  Value/Control) │
                                               └─────────────────┘
```

### 2. Data Flow Architecture

The system implements a **Request-Response Pipeline** with the following stages:

1. **Input Processing**: User input → Frontend validation → API endpoint
2. **Agent Selection**: LangChain Supervisor analyzes intent → Routes to appropriate agent
3. **Agent Processing**: Specialized agent processes query → Generates structured response
4. **Response Standardization**: Response validation → Schema compliance → Frontend rendering
5. **State Management**: Session persistence → Database operations → Context maintenance

## Detailed Component Analysis

### 1. Frontend Layer (`templates/scene.html`)

**Purpose**: Provides the user interface for VR dental planning interactions.

**Key Components**:
- **Chat Interface**: Real-time messaging system with conversation history
- **Notes Management**: Interactive note-taking with state management
- **Session Management**: Maintains user session context across interactions

**Technical Implementation**:
```javascript
class DentalChatbot {
    constructor() {
        this.currentSession = this.generateSessionId();
        this.conversationHistory = [];
        this.notesActive = false;
    }
    
    async sendMessage(text) {
        // Sends user input to backend API
        // Handles response rendering and state updates
    }
    
    async startNotesSession() {
        // Initiates notes session via /v1/notes/start API
        // Manages UI state transitions
    }
}
```

**State Management**:
- **Session Persistence**: Each user interaction maintains session context
- **Notes State**: Tracks active/inactive notes mode with UI transitions
- **Conversation History**: Maintains context for contextual agent selection

### 2. API Layer (`app/routes.py`)

**Purpose**: RESTful API gateway handling all client-server communications.

**Key Endpoints**:
- `/api/v1/chat`: Main chat interface endpoint
- `/api/v1/notes/*`: Notes management endpoints (start/add/end/list)
- `/api/v1/ingest`: Document ingestion for RAG system

**Technical Implementation**:
```python
@api_bp.post("/v1/chat")
def chat():
    # Validates request schema
    # Routes to DecisionRouter
    # Standardizes response format
    # Returns structured JSON response
```

**Response Standardization**:
The API implements a **Response Standardization Layer** that ensures consistent output format:
```python
standardized_response = {
    "agent": validated_response.get("agent", "Dental AI"),
    "intent": validated_response.get("intent", "General Response"),
    "message": response_text,  # Primary response field
    "confidence": validated_response.get("confidence", {}),
    "json_output": validated_response,
    "session_id": req.sessionId,
    "timestamp": datetime.now().isoformat()
}
```

### 3. Decision Router (`app/scene/router.py`)

**Purpose**: Central routing mechanism that determines which specialized agent should handle user queries.

**Architecture Pattern**: **Strategy Pattern** with dynamic agent selection.

**Technical Implementation**:
```python
class DecisionRouter:
    def __init__(self):
        self.agents = {
            'info': info_agent,
            'notes': notes_agent,
            'value': value_agent,
            'control': control_agent
        }
    
    def route(self, text: str, session_id: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        # 1. LangChain Supervisor selects appropriate agent
        agent_name = langchain_supervisor.select_agent(text, conversation_history)
        
        # 2. Retrieve selected agent
        agent = self.agents.get(agent_name, info_agent)
        
        # 3. Process query with selected agent
        response = agent.process(text, conversation_history, session_id)
        
        # 4. Add session context and log response
        return response
```

**Context Awareness**:
- **Conversation History**: Maintains context across multiple interactions
- **Session Management**: Tracks user session for personalized responses
- **Agent Selection**: Uses conversation context to improve routing accuracy

### 4. LangChain Supervisor (`app/agent/langchain_supervisor.py`)

**Purpose**: LLM-based intelligent agent selection system using LangChain framework.

**Architecture Pattern**: **Chain of Responsibility** with LLM-based decision making.

**Technical Implementation**:
```python
class LangChainSupervisor:
    def select_agent(self, query: str, conversation_history: List[Dict] = None) -> str:
        # 1. Build context from conversation history
        context = self._build_context(query, conversation_history)
        
        # 2. Create system prompt with agent descriptions
        system_prompt = self._get_system_prompt()
        
        # 3. Use LLM to analyze query and select agent
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        # 4. Parse and validate agent selection
        return self._parse_agent_selection(response.content)
```

**Agent Selection Logic**:
The supervisor uses **Contextual Analysis** to determine appropriate agent routing:

1. **Info Agent**: Dental anatomy, definitions, explanations
2. **Notes Agent**: Note-taking, recording, documentation
3. **Value Agent**: Image properties (brightness, contrast, opacity)
4. **Control Agent**: VR tools, overlays, implant selection

**Context Rules**:
```python
# Implant-related queries maintain context
if previous_message_about_implants and user_provides_numbers:
    route_to_control_agent()

# Social responses route to conversational agent
if query in ['thank you', 'thanks', 'ok', 'okay']:
    route_to_info_agent()
```

### 5. Specialized Agents

#### 5.1 Base Agent (`app/agent/base_agent.py`)

**Purpose**: Abstract base class providing common functionality for all specialized agents.

**Design Pattern**: **Template Method Pattern** with common processing pipeline.

**Technical Implementation**:
```python
class BaseAgent:
    def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
        # 1. Build context from query and history
        context = self._build_context(query, conversation_history)
        
        # 2. Load agent-specific schema
        schema = self._load_schema()
        
        # 3. Execute LLM with structured output
        response = self._execute_llm(context, schema)
        
        # 4. Validate and standardize response
        return self._validate_response(response)
```

**Common Features**:
- **Schema Validation**: Ensures response format compliance
- **Context Building**: Constructs relevant context from conversation history
- **Error Handling**: Graceful fallback mechanisms
- **Response Standardization**: Consistent output format across agents

#### 5.2 Info Agent (`app/agent/info_agent.py`)

**Purpose**: Handles dental information queries and conversational responses.

**Specialized Functionality**:
```python
def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
    # Handle conversational responses
    conversational_responses = {
        'thank you': "You're welcome! Happy to help with your dental planning.",
        'thanks': "You're welcome!",
        'ok': "Got it! Let me know if you need anything else."
    }
    
    # Check for conversational patterns
    for phrase, response in conversational_responses.items():
        if phrase in query_lower:
            return self._create_conversational_response(response)
    
    # Fall back to standard LLM processing
    return super().process(query, conversation_history, session_id)
```

**Response Schema**:
```json
{
    "type": "answer",
    "agent": "Info Agent",
    "intent": "dental_information",
    "message": "Response text",
    "confidence": 0.9,
    "context_used": true,
    "sources": ["source1", "source2"]
}
```

#### 5.3 Notes Agent (`app/agent/notes_agent.py`)

**Purpose**: Manages note-taking functionality with database persistence.

**State Management**:
```python
def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
    # Start notes requests
    if any(phrase in query_lower for phrase in ['start taking notes', 'start notes']):
        return {
            "type": "note_action",
            "function": "start_notes",
            "message": "Notes are now active! You can type your notes below.",
            "state": "on",
            "confidence": 0.9
        }
    
    # Retrieve notes requests
    if any(phrase in query_lower for phrase in ['show me my notes', 'my notes']):
        notes = Note.query.filter_by(session_id=session_id, finalized=True).all()
        return self._format_notes_response(notes)
```

**Database Integration**:
- **Session Management**: Tracks notes per user session
- **Persistence**: Stores notes in SQLite database
- **Retrieval**: Queries database for session-specific notes
- **Finalization**: Marks notes as complete when session ends

#### 5.4 Control Agent (`app/agent/control_agent.py`)

**Purpose**: Handles VR environment controls and implant selection.

**Implant Selection Logic**:
```python
def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
    # Handle implant size rejection
    if any(phrase in query_lower for phrase in ['i do not want', "don't want", 'not that size']):
        parsed = self._parse_implant_size(query)
        return {
            "type": "implant_select",
            "target": parsed['target'],
            "value": parsed['value'],
            "message": f"Selecting new implant size {parsed['height']}x{parsed['length']}."
        }
```

**Context-Aware Processing**:
- **Implant Context**: Maintains context for implant-related queries
- **Size Parsing**: Extracts dimensions from natural language
- **State Management**: Tracks VR environment state

#### 5.5 Value Agent (`app/agent/value_agent.py`)

**Purpose**: Controls image properties and visual settings in VR environment.

**Value Adjustment Logic**:
```python
def _parse_value_command(self, query: str) -> Dict[str, Any]:
    # Parse brightness, contrast, opacity adjustments
    # Handle increase/decrease operations
    # Validate value ranges (0-100)
    # Return structured command
```

**Supported Operations**:
- **Brightness**: 0-100 range adjustments
- **Contrast**: Percentage-based modifications
- **Opacity**: Transparency level controls

### 6. Data Layer

#### 6.1 Database Models (`app/models.py`)

**Purpose**: SQLAlchemy ORM models for data persistence.

**Key Models**:
```python
class Session(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(64), db.ForeignKey("sessions.id"))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finalized = db.Column(db.Boolean, default=False)

class Document(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id"))
    text = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.LargeBinary)
```

#### 6.2 Notes Service (`app/notes/service.py`)

**Purpose**: Business logic layer for notes management.

**Service Operations**:
```python
class NotesService:
    def start(self, session_id: str) -> None:
        # Create session if not exists
        # Initialize notes session
    
    def add(self, session_id: str, text: str) -> Note:
        # Add note to database
        # Return created note object
    
    def end(self, session_id: str) -> List[Note]:
        # Finalize all notes in session
        # Mark as completed
    
    def list(self, session_id: str) -> List[Note]:
        # Retrieve all notes for session
        # Return ordered by creation time
```

### 7. RAG (Retrieval-Augmented Generation) System

#### 7.1 Hybrid Retrieval (`app/rag/retriever.py`)

**Purpose**: Implements hybrid retrieval combining semantic and lexical search.

**Architecture**:
```python
class HybridRetriever:
    def __init__(self):
        self.semantic_retriever = FAISSRetriever()  # Vector-based
        self.lexical_retriever = BM25Retriever()    # Keyword-based
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        # 1. Semantic search using embeddings
        semantic_results = self.semantic_retriever.search(query, top_k)
        
        # 2. Lexical search using BM25
        lexical_results = self.lexical_retriever.search(query, top_k)
        
        # 3. Combine and rank results
        return self._combine_results(semantic_results, lexical_results)
```

**Technical Implementation**:
- **Semantic Search**: Uses Ollama embeddings with FAISS vector database
- **Lexical Search**: BM25-like algorithm for keyword matching
- **Hybrid Ranking**: Combines both approaches for optimal retrieval

### 8. Configuration System

#### 8.1 Schema-Based Configuration

**Purpose**: Externalized configuration using JSON schemas for each agent.

**Schema Structure**:
```json
{
    "type": "object",
    "properties": {
        "type": {"type": "string", "default": "answer"},
        "agent": {"type": "string"},
        "intent": {"type": "string"},
        "message": {"type": "string"},
        "confidence": {"type": "number"},
        "context_used": {"type": "boolean"}
    }
}
```

**Benefits**:
- **Flexibility**: Easy modification without code changes
- **Validation**: Automatic schema validation
- **Consistency**: Standardized response formats

## Technical Implementation Details

### 1. Session Management

**Session Lifecycle**:
1. **Creation**: Unique session ID generated on first interaction
2. **Persistence**: Session maintained across multiple requests
3. **Context**: Conversation history stored per session
4. **Cleanup**: Sessions can be archived or deleted

**Implementation**:
```python
def generate_session_id() -> str:
    return str(uuid.uuid4())

def get_session_context(session_id: str) -> List[Dict]:
    return Session.query.get(session_id).conversation_history
```

### 2. Error Handling and Fallbacks

**Multi-Level Error Handling**:
1. **Agent Level**: Individual agent error handling
2. **Router Level**: Fallback to default agent
3. **API Level**: Graceful error responses
4. **Frontend Level**: User-friendly error messages

**Fallback Strategy**:
```python
def route(self, text: str, session_id: str) -> Dict[str, Any]:
    try:
        agent_name = langchain_supervisor.select_agent(text)
        agent = self.agents.get(agent_name, info_agent)  # Default fallback
        return agent.process(text, session_id)
    except Exception as e:
        return self._create_error_response(str(e))
```

### 3. Response Standardization

**Standardization Pipeline**:
1. **Agent Response**: Raw agent output
2. **Schema Validation**: Pydantic model validation
3. **Field Standardization**: Consistent field names
4. **Response Assembly**: Final standardized response

**Implementation**:
```python
def standardize_response(agent_response: Dict) -> Dict:
    # Extract primary response text
    response_text = (
        agent_response.get("answer") or
        agent_response.get("message") or
        agent_response.get("response")
    )
    
    # Create standardized response
    return {
        "agent": agent_response.get("agent", "Dental AI"),
        "intent": agent_response.get("intent", "General Response"),
        "message": response_text,
        "confidence": agent_response.get("confidence", {}),
        "json_output": agent_response,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    }
```

## Performance Considerations

### 1. Caching Strategy

**Multi-Level Caching**:
- **Agent Responses**: Cache frequent responses
- **Database Queries**: Cache session data
- **LLM Responses**: Cache similar queries

### 2. Database Optimization

**Indexing Strategy**:
- **Session ID**: Primary key indexing
- **Note Timestamps**: Temporal query optimization
- **Document Embeddings**: Vector similarity search

### 3. Scalability Considerations

**Horizontal Scaling**:
- **Stateless Agents**: No shared state between instances
- **Database Sharding**: Session-based partitioning
- **Load Balancing**: Multiple agent instances

## Security Considerations

### 1. Input Validation

**Multi-Layer Validation**:
- **Frontend**: Client-side input sanitization
- **API**: Pydantic schema validation
- **Database**: SQL injection prevention

### 2. Session Security

**Session Management**:
- **Unique IDs**: UUID-based session identification
- **Timeout**: Automatic session expiration
- **Isolation**: Session data isolation

## Future Enhancements

### 1. Advanced Features

**Planned Enhancements**:
- **Multi-Modal Input**: Voice and gesture recognition
- **Real-Time Collaboration**: Multi-user sessions
- **Advanced Analytics**: Usage pattern analysis
- **Machine Learning**: Continuous model improvement

### 2. Integration Opportunities

**External Integrations**:
- **DICOM Support**: Medical imaging integration
- **CAD Systems**: 3D modeling integration
- **EHR Systems**: Electronic health records
- **Cloud Services**: Scalable cloud deployment

## Conclusion

The Medallion Agents system represents a sophisticated approach to multi-agent AI systems in healthcare applications. By combining LLM-based supervision with specialized domain agents, the system provides intelligent, context-aware assistance for VR dental planning scenarios.

**Key Strengths**:
- **Modular Architecture**: Easy to extend and maintain
- **Context Awareness**: Maintains conversation context
- **Robust Error Handling**: Graceful degradation
- **Scalable Design**: Supports horizontal scaling

**Technical Innovation**:
- **Hybrid RAG**: Combines semantic and lexical search
- **Dynamic Agent Selection**: LLM-based routing
- **State Management**: Persistent session context
- **Response Standardization**: Consistent API responses

The system demonstrates effective application of modern AI techniques in a specialized domain, providing a foundation for advanced VR-based medical applications.
