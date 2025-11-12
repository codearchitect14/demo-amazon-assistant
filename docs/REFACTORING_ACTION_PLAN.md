# Refactoring Action Plan

## Phase 1: Critical Issues Resolution (Week 1-2)

### 1.1 Split `rag/rag_utils.py` (Priority: Critical)

**Current Problem**: 1971-line file with multiple responsibilities

**Action Steps**:

1. **Create new directory structure**:
```bash
mkdir -p rag/resilience rag/llm rag/memory rag/utils
```

2. **Extract Circuit Breaker** (`rag/resilience/circuit_breaker.py`):
```python
import time
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

3. **Extract Retry Handler** (`rag/resilience/retry_handler.py`):
```python
import time
import logging
from typing import Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class RetryHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                    time.sleep(delay)
        
        raise last_exception
```

4. **Extract LLM Client** (`rag/llm/client.py`):
```python
import logging
from typing import List, Dict, Any
from groq import Groq, AsyncGroq
from app.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.sync_client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)

    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = self.sync_client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    async def generate_response_async(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Async LLM generation error: {e}")
            raise
```

5. **Extract Memory Base** (`rag/memory/base.py`):
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MemoryStrategy(ABC):
    @abstractmethod
    def add_interaction(self, session_id: str, question: str, answer: str, context: str = "", metadata: Dict[str, Any] = None):
        pass

    @abstractmethod
    def get_recent_context(self, session_id: str, max_entries: int = 3) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def clear_session(self, session_id: str):
        pass

    @abstractmethod
    def get_memory_stats(self) -> Dict[str, Any]:
        pass
```

6. **Extract Business Logic** (`rag/utils/business_logic.py`):
```python
import logging
from typing import List, Dict, Any
from rag.llm.client import LLMClient
from rag.memory.base import MemoryStrategy

logger = logging.getLogger(__name__)

def run_rag_pipeline_sync(
    retriever,
    llm_client: LLMClient,
    memory: MemoryStrategy,
    memory_enabled: bool,
    model: str,
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "multi",
) -> Dict[str, Any]:
    """Synchronous RAG pipeline execution"""
    try:
        # Retrieve context
        context = retrieve_context_sync(retriever, question, top_k, retrieval_method)
        
        # Get conversation history
        conversation_history = ""
        if memory_enabled and session_id:
            recent_context = memory.get_recent_context(session_id)
            conversation_history = format_conversation_history(recent_context)
        
        # Generate answer
        answer = generate_answer_sync(llm_client, context, question, session_id, conversation_history)
        
        # Store in memory
        if memory_enabled and session_id:
            memory.add_interaction(session_id, question, answer, context)
        
        return {
            "question": question,
            "answer": answer,
            "context": context,
            "metadata": {
                "memory_enabled": memory_enabled,
                "has_conversation_history": bool(conversation_history),
                "retrieval_method": retrieval_method,
                "top_k": top_k
            }
        }
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        raise
```

### 1.2 Implement Shared Utilities

**Create** `shared/utils/serialization.py`:
```python
import numpy as np
from typing import Any, Dict, List

class NumpySerializer:
    @staticmethod
    def convert_numpy_types(obj: Any) -> Any:
        """Convert numpy types to Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {key: NumpySerializer.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [NumpySerializer.convert_numpy_types(item) for item in obj]
        else:
            return obj
```

**Create** `shared/utils/error_handling.py`:
```python
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    def handle_extraction_error(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return []
        return wrapper

    @staticmethod
    def handle_api_error(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"API error in {func.__name__}: {e}")
                raise
        return wrapper
```

### 1.3 Split API Layer

**Create** `app/api/routes/chat.py`:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.rag_service import RAGService

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    retrieval_method: str = "title_first"
    session_id: str = None
    use_advanced_features: bool = False

class ChatResponse(BaseModel):
    answer: str
    context: str
    metadata: dict

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        rag_service = RAGService()  # Get from DI container
        result = await rag_service.process_chat(request)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Create** `app/services/rag_service.py`:
```python
import logging
from typing import Dict, Any
from app.config import Config
from rag.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, config: Config):
        self.config = config
        self.pipeline = RAGPipeline(
            enable_memory=True,
            memory_type="langchain"
        )

    async def process_chat(self, request) -> Dict[str, Any]:
        try:
            result = await self.pipeline.run_rag_pipeline_async(
                question=request.query,
                session_id=request.session_id,
                top_k=request.top_k,
                retrieval_method=request.retrieval_method,
            )
            return result
        except Exception as e:
            logger.error(f"RAG service error: {e}")
            raise
```

## Phase 2: Dependency Injection Implementation (Week 3)

### 2.1 Create Dependency Injection Container

**Create** `core/container.py`:
```python
from typing import Dict, Any, Type, TypeVar
from app.config import Config
from rag.llm.client import LLMClient
from rag.retriever import MultiVectorRetriever
from rag.memory.base import MemoryStrategy
from rag.memory.conversation import ConversationMemory

T = TypeVar('T')

class Container:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._config = Config()

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service"""
        self._singletons[interface] = implementation

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service"""
        self._services[interface] = implementation

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service from the container"""
        if interface in self._singletons:
            if interface not in self._services:
                self._services[interface] = self._singletons[interface]()
            return self._services[interface]
        
        if interface in self._services:
            return self._services[interface]()
        
        raise Exception(f"Service {interface} not registered")

    def configure_services(self) -> None:
        """Configure all services"""
        # Register core services
        self.register_singleton(LLMClient, lambda: LLMClient(self._config.GROQ_API_KEY))
        self.register_singleton(MultiVectorRetriever, lambda: MultiVectorRetriever())
        self.register_singleton(MemoryStrategy, lambda: ConversationMemory())
```

### 2.2 Update API to Use DI

**Update** `app/api.py`:
```python
from fastapi import FastAPI, Depends
from core.container import Container

app = FastAPI()
container = Container()
container.configure_services()

def get_rag_service():
    return container.resolve(RAGService)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    return await rag_service.process_chat(request)
```

## Phase 3: CQRS Implementation (Week 4)

### 3.1 Create Command/Query Structure

**Create** `application/commands/base.py`:
```python
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class CommandResult:
    success: bool
    data: Any = None
    error: str = None

class Command(ABC):
    @abstractmethod
    def execute(self) -> CommandResult:
        pass
```

**Create** `application/queries/base.py`:
```python
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class QueryResult:
    success: bool
    data: Any = None
    error: str = None

class Query(ABC):
    @abstractmethod
    def execute(self) -> QueryResult:
        pass
```

### 3.2 Implement Chat Commands

**Create** `application/commands/chat_command.py`:
```python
from dataclasses import dataclass
from application.commands.base import Command, CommandResult
from rag.rag_pipeline import RAGPipeline

@dataclass
class ChatCommand(Command):
    query: str
    session_id: str
    top_k: int = 5
    retrieval_method: str = "title_first"

    def execute(self) -> CommandResult:
        try:
            pipeline = RAGPipeline()
            result = pipeline.run_rag_pipeline(
                question=self.query,
                session_id=self.session_id,
                top_k=self.top_k,
                retrieval_method=self.retrieval_method,
            )
            return CommandResult(success=True, data=result)
        except Exception as e:
            return CommandResult(success=False, error=str(e))
```

### 3.3 Implement Search Queries

**Create** `application/queries/search_query.py`:
```python
from dataclasses import dataclass
from application.queries.base import Query, QueryResult
from rag.retriever import MultiVectorRetriever

@dataclass
class SearchQuery(Query):
    query: str
    top_k: int = 10
    retrieval_method: str = "title_first"

    def execute(self) -> QueryResult:
        try:
            retriever = MultiVectorRetriever()
            results = retriever.title_first_search(
                query=self.query,
                top_products=self.top_k
            )
            return QueryResult(success=True, data=results)
        except Exception as e:
            return QueryResult(success=False, error=str(e))
```

## Phase 4: Resource Management (Week 5)

### 4.1 Implement Resource Manager

**Create** `core/resource_manager.py`:
```python
import logging
from typing import List, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ResourceManager:
    def __init__(self):
        self._resources: List[Any] = []
        self._cleanup_handlers: List[callable] = []

    def register_resource(self, resource: Any, cleanup_handler: callable = None):
        """Register a resource with optional cleanup handler"""
        self._resources.append(resource)
        if cleanup_handler:
            self._cleanup_handlers.append(cleanup_handler)

    def cleanup(self):
        """Cleanup all registered resources"""
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error during resource cleanup: {e}")

    @contextmanager
    def managed_resources(self):
        """Context manager for resource management"""
        try:
            yield self
        finally:
            self.cleanup()
```

### 4.2 Update Embedding Cache

**Update** `rag/embedding_cache.py`:
```python
from core.resource_manager import ResourceManager

class EmbeddingModelCache:
    def __init__(self, model_name: str = None, lifetime_hours: int = 2):
        # ... existing initialization ...
        self.resource_manager = ResourceManager()
        self.resource_manager.register_resource(self, self.cleanup)

    def cleanup(self):
        """Cleanup resources"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._shutdown_event.set()
            self._cleanup_thread.join(timeout=5)
        
        if self.model:
            del self.model
            self.model = None
```

## Phase 5: Testing and Validation (Week 6)

### 5.1 Create Integration Tests

**Create** `tests/integration/test_rag_pipeline.py`:
```python
import pytest
from rag.rag_pipeline import RAGPipeline
from app.config import Config

class TestRAGPipeline:
    @pytest.fixture
    def pipeline(self):
        return RAGPipeline(enable_memory=True)

    def test_basic_chat(self, pipeline):
        result = pipeline.run_rag_pipeline(
            question="What are some good wireless headphones?",
            session_id="test_session"
        )
        
        assert result["answer"] is not None
        assert result["context"] is not None
        assert result["metadata"]["memory_enabled"] is True

    def test_memory_persistence(self, pipeline):
        # First query
        result1 = pipeline.run_rag_pipeline(
            question="What are wireless headphones?",
            session_id="test_session"
        )
        
        # Second query referencing first
        result2 = pipeline.run_rag_pipeline(
            question="Tell me more about the ones you mentioned",
            session_id="test_session"
        )
        
        assert result2["metadata"]["has_conversation_history"] is True
```

### 5.2 Create Unit Tests

**Create** `tests/unit/test_memory.py`:
```python
import pytest
from rag.memory.conversation import ConversationMemory

class TestConversationMemory:
    @pytest.fixture
    def memory(self):
        return ConversationMemory()

    def test_add_interaction(self, memory):
        memory.add_interaction(
            session_id="test",
            question="What is this?",
            answer="A test response"
        )
        
        context = memory.get_recent_context("test")
        assert len(context) == 1
        assert context[0]["question"] == "What is this?"

    def test_clear_session(self, memory):
        memory.add_interaction("test", "Q", "A")
        memory.clear_session("test")
        
        context = memory.get_recent_context("test")
        assert len(context) == 0
```

## Implementation Timeline

| Week | Task | Deliverables |
|------|------|--------------|
| 1 | Split rag_utils.py | Separate modules for resilience, LLM, memory, utils |
| 2 | Implement shared utilities | Serialization, error handling utilities |
| 3 | Dependency injection | Container implementation, service registration |
| 4 | CQRS pattern | Command/query separation, handlers |
| 5 | Resource management | Resource manager, cleanup handlers |
| 6 | Testing | Integration and unit tests |

## Success Metrics

1. **Code Quality**:
   - Reduce cyclomatic complexity by 30%
   - Achieve 90%+ test coverage
   - Zero critical SonarQube issues

2. **Performance**:
   - Maintain or improve response times
   - Reduce memory usage by 20%
   - Eliminate memory leaks

3. **Maintainability**:
   - Reduce file sizes to <500 lines
   - Implement proper separation of concerns
   - Add comprehensive logging

4. **Scalability**:
   - Support horizontal scaling
   - Implement proper resource management
   - Add monitoring and metrics

## Risk Mitigation

1. **Breaking Changes**: Implement changes incrementally with feature flags
2. **Performance Impact**: Monitor performance during refactoring
3. **Testing Coverage**: Maintain comprehensive test suite
4. **Rollback Plan**: Keep previous version as backup
5. **Documentation**: Update documentation as changes are made

This action plan provides a structured approach to improving the codebase architecture while maintaining functionality and minimizing disruption. 