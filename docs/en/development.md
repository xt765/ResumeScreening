# Development Guide

## Development Environment Setup

### 1. Install Dependency Tools

```bash
# Install Python 3.13+
# Windows: Download from python.org
# macOS: brew install python@3.13
# Linux: sudo apt install python3.13

# Install uv package manager
pip install uv

# Install Docker Desktop
# Download from docker.com
```

### 2. Clone Project

```bash
git clone <repository-url>
cd ResumeScreening
```

### 3. Install Project Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Install development dependencies
uv sync --group dev
```

### 4. Configure Development Environment

```bash
# Copy environment variable config
cp .env.example .env

# Edit .env file, configure local development parameters
```

### 5. Start Dependency Services

```bash
# Start MySQL, Redis, MinIO
docker-compose up -d mysql redis minio
```

### 6. Initialize Database

```bash
# Create database tables
uv run python scripts/init_db.py

# Create admin account
uv run python scripts/init_admin.py
```

### 7. Start Development Services

```bash
# Terminal 1: Start backend
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend
cd frontend-new && python -m http.server 3000
```

## Project Structure Details

```
ResumeScreening/
├── docs/                      # Project documentation
├── frontend-new/              # Frontend code
│   ├── index.html             # Entry page
│   ├── css/                   # Style files
│   │   ├── style.css          # Main styles
│   │   └── users.css          # User management styles
│   └── js/                    # JavaScript
│       ├── app.js             # App entry, routing
│       ├── api.js             # API wrapper
│       └── pages/             # Page modules
│           ├── login.js       # Login page
│           ├── dashboard.js   # Dashboard
│           ├── upload.js      # Upload screening
│           ├── talents.js     # Talent management
│           ├── conditions.js  # Condition management
│           ├── analysis.js    # Intelligent analysis
│           ├── monitor.js     # System monitoring
│           └── users.js       # User management
├── src/                       # Backend code
│   ├── api/                   # API layer
│   │   ├── main.py            # FastAPI application
│   │   ├── deps.py            # Dependency injection
│   │   └── v1/                # v1 version
│   ├── core/                  # Core modules
│   │   ├── config.py          # Configuration management
│   │   ├── security.py        # Security encryption
│   │   ├── auth.py            # Authentication logic
│   │   ├── exceptions.py      # Exception definitions
│   │   ├── logger.py          # Logging config
│   │   └── tasks.py           # Task management
│   ├── models/                # SQLAlchemy models
│   │   ├── base.py            # Base model
│   │   ├── user.py            # User model
│   │   ├── talent.py          # Talent model
│   │   └── condition.py       # Condition model
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business services
│   │   ├── nlp_parser.py      # NLP parsing
│   │   ├── log_service.py     # Log service
│   │   └── metrics_service.py # Metrics service
│   ├── storage/               # Storage clients
│   │   ├── chroma_client.py   # ChromaDB
│   │   ├── minio_client.py    # MinIO
│   │   └── redis_client.py    # Redis
│   ├── utils/                 # Utility functions
│   │   ├── embedding.py       # Embedding service
│   │   ├── rag_service.py     # RAG service
│   │   ├── face_detector.py   # Face detection
│   │   └── school_tier_data.py# School tier data
│   ├── parsers/               # Document parsing
│   │   └── document_parser.py # Parser
│   └── workflows/             # LangGraph workflow
│       ├── state.py           # State definition
│       ├── resume_workflow.py # Workflow orchestration
│       ├── parse_extract_node.py
│       ├── filter_node.py
│       ├── store_node.py
│       └── cache_node.py
├── scripts/                   # Script tools
│   ├── init_db.py             # Initialize database
│   ├── init_admin.py          # Create admin
│   └── clear_all_databases.py # Clear data
├── tests/                     # Test code
│   └── test_data/             # Test data
├── pyproject.toml             # Project config
└── docker-compose.yml         # Docker orchestration
```

## Code Standards

### Python Code Standards

#### 1. Naming Conventions

```python
# Module name: lowercase with underscores
# my_module.py

# Class name: PascalCase
class TalentInfo:
    pass

# Function name: lowercase with underscores
def get_talent_by_id(talent_id: str) -> TalentInfo | None:
    pass

# Constants: UPPERCASE with underscores
MAX_FILE_SIZE = 10 * 1024 * 1024

# Private attributes: single underscore prefix
self._internal_value = None
```

#### 2. Type Annotations

```python
from typing import Any

# Function parameter and return type annotations
def process_resume(
    file_path: str,
    condition_id: str | None = None,
) -> dict[str, Any]:
    pass

# Class attribute type annotations
class ResumeState(BaseModel):
    file_path: str
    text_content: str | None = None
    skills: list[str] = Field(default_factory=list)
```

#### 3. Docstrings

```python
def extract_candidate_info(text: str) -> dict[str, Any]:
    """Extract candidate information from resume text.

    Use LLM to extract structured information from unstructured
    resume text, including name, contact, education, work experience, etc.

    Args:
        text: Resume text content.

    Returns:
        dict[str, Any]: Extracted candidate info dictionary.

    Raises:
        LLMException: Raised when LLM call fails.

    Example:
        >>> info = extract_candidate_info("John Doe, Tsinghua University...")
        >>> print(info["name"])
        'John Doe'
    """
    pass
```

#### 4. Function Length Limit

- Single function no more than 50 lines
- Split complex logic into multiple small functions
- Use early returns to reduce nesting

```python
# Good practice
def process_file(file_path: str) -> dict[str, Any]:
    if not file_path:
        return {"error": "File path is empty"}

    if not Path(file_path).exists():
        return {"error": "File does not exist"}

    content = read_file(file_path)
    result = parse_content(content)

    return result
```

### JavaScript Code Standards

#### 1. Naming Conventions

```javascript
// Variable name: camelCase
const talentList = [];

// Function name: camelCase
function getTalentById(id) {
    // ...
}

// Constants: UPPERCASE with underscores
const MAX_FILES = 50;

// Class name: PascalCase
class TalentManager {
    // ...
}

// Private method: underscore prefix
_internalMethod() {
    // ...
}
```

#### 2. Comment Standards

```javascript
/**
 * Handle file selection event
 * @param {FileList} files - Selected file list
 * @returns {void}
 */
handleFilesSelect(files) {
    // Validate file types
    const allowedTypes = ['pdf', 'docx', 'doc'];
    // ...
}
```

## Testing Guide

### Testing Framework

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage report

### Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_workflows.py

# Run specific test case
uv run pytest tests/test_workflows.py::test_parse_extract_node

# Show verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=src --cov-report=html
```

### Test Example

```python
import pytest
from src.workflows.state import ResumeState

@pytest.fixture
def sample_state() -> ResumeState:
    """Create test state instance."""
    return ResumeState(
        file_path="/tmp/test.pdf",
        file_type="pdf",
    )

@pytest.mark.asyncio
async def test_parse_extract_node(sample_state: ResumeState):
    """Test parse extract node."""
    from src.workflows.parse_extract_node import ParseExtractNode

    node = ParseExtractNode()
    result = await node.execute(sample_state)

    assert result.success
    assert result.updates.get("text_content") is not None
```

### Test Coverage

Project requires test coverage >= 95%.

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=html

# View HTML report
# Open htmlcov/index.html
```

## Code Checking

### Ruff Formatting

```bash
# Format code
uv run ruff format src/

# Check code style
uv run ruff check src/

# Auto fix
uv run ruff check src/ --fix
```

### Type Checking

```bash
# Run type checking
uv run basedpyright src/
```

## Adding New Features

### 1. Add New API Endpoint

```python
# src/api/v1/talents.py

@router.get(
    "/{talent_id}/resume",
    summary="Get resume original text",
)
async def get_resume_content(
    talent_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[dict[str, Any]]:
    """Get talent resume original content."""
    # Implementation logic
    pass
```

### 2. Add New Workflow Node

```python
# src/workflows/custom_node.py

from src.workflows.state import ResumeState, NodeResult

class CustomNode:
    """Custom processing node."""

    async def execute(self, state: ResumeState) -> NodeResult:
        """Execute node logic.

        Args:
            state: Workflow state

        Returns:
            NodeResult: Node execution result
        """
        try:
            # Processing logic
            return NodeResult(
                success=True,
                updates={"custom_field": "value"},
            )
        except Exception as e:
            return NodeResult(
                success=False,
                error=str(e),
            )
```

### 3. Add New Data Model

```python
# src/models/custom.py

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

class CustomModel(Base, TimestampMixin):
    """Custom data model."""

    __tablename__ = "custom_table"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### 4. Add Frontend Page

```javascript
// frontend-new/js/pages/custom.js

const CustomPage = {
    async render() {
        return `
            <div class="custom-page">
                <h2>Custom Page</h2>
                <!-- Page content -->
            </div>
        `;
    },

    async init() {
        // Initialization logic
    },

    async loadData() {
        // Load data
    }
};
```

## Debugging Tips

### 1. Backend Debugging

```python
from loguru import logger

# Use logger for debugging
logger.debug(f"Processing file: {file_path}")
logger.info(f"Extracted {len(skills)} skills")
logger.warning(f"Condition not found: {condition_id}")
logger.error(f"Processing failed: {error}")
```

### 2. Frontend Debugging

```javascript
// Use console for debugging
console.log('Processing data:', data);
console.warn('Warning message');
console.error('Error message');

// Use debugger breakpoint
debugger;
```

### 3. Database Debugging

```bash
# Enter MySQL container
docker-compose exec mysql mysql -u root -p

# Query data
SELECT * FROM talent_info LIMIT 10;

# View execution plan
EXPLAIN SELECT * FROM talent_info WHERE name = 'John Doe';
```

## Common Issues

### 1. Dependency Installation Failure

```bash
# Clear cache and reinstall
uv cache clean
uv sync
```

### 2. Database Connection Failure

```bash
# Check if MySQL is running
docker-compose ps mysql

# View logs
docker-compose logs mysql
```

### 3. LLM Call Failure

- Check if API Key is correct
- Check network connection
- Check API quota

### 4. Frontend CORS Issues

Development environment has CORS configured in backend, production needs Nginx configuration.

## Git Commit Standards

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type Description

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation update |
| style | Code format adjustment |
| refactor | Code refactoring |
| test | Test related |
| chore | Build/tool related |

### Example

```
feat(api): Add resume batch export feature

- Support PDF/Excel format export
- Support batch export by screening conditions
- Add export progress display

Closes #123
```
