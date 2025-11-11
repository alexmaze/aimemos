# AI Memos

An AI-based personal knowledge base service built with FastAPI and PocketFlow.

## Tech Stack

- **Python 3.12+**: Modern Python features
- **uv**: Fast Python package manager
- **FastAPI**: High-performance web framework
- **PocketFlow**: AI workflow framework
- **Pydantic**: Data validation and settings management

## Features

- Create, read, update, and delete memos
- Search memos by title, content, or tags
- RESTful API with automatic documentation
- In-memory storage (easily extendable to persistent storage)
- Health check endpoints

## Installation

### Prerequisites

- Python 3.12 or higher
- uv package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/alexmaze/aimemos.git
cd aimemos
```

2. Install dependencies using uv:
```bash
uv sync
```

3. (Optional) Copy and configure the environment file:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Usage

### Running the Server

Start the server using uv:

```bash
uv run aimemos
```

Or run directly with Python:

```bash
uv run python -m aimemos.main
```

The server will start on `http://0.0.0.0:8000` by default.

### API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

### API Endpoints

#### Root & Health

- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint

#### Memos

- `POST /api/v1/memos` - Create a new memo
- `GET /api/v1/memos` - List all memos (with pagination)
- `GET /api/v1/memos/search?q=query` - Search memos
- `GET /api/v1/memos/{id}` - Get a specific memo
- `PUT /api/v1/memos/{id}` - Update a memo
- `DELETE /api/v1/memos/{id}` - Delete a memo

### Example Usage

Create a memo:
```bash
curl -X POST "http://localhost:8000/api/v1/memos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Memo",
    "content": "This is the content of my memo",
    "tags": ["personal", "test"]
  }'
```

List memos:
```bash
curl "http://localhost:8000/api/v1/memos"
```

Search memos:
```bash
curl "http://localhost:8000/api/v1/memos/search?q=first"
```

### Demo Script

A demo script is provided to showcase the API functionality:

```bash
# Install demo dependencies
uv sync --extra demo

# Run the demo (make sure the server is running first)
uv run python demo.py
```

## Development

### Project Structure

```
aimemos/
├── aimemos/           # Main package
│   ├── __init__.py    # Package initialization
│   ├── app.py         # FastAPI application
│   ├── config.py      # Configuration management
│   ├── main.py        # Entry point
│   ├── models.py      # Pydantic models
│   ├── routes.py      # API routes
│   └── storage.py     # Data storage layer
├── demo.py            # Demo script
├── .env.example       # Example environment file
├── pyproject.toml     # Project dependencies
└── uv.lock            # Lock file for dependencies
```

### Configuration

Configuration is managed through environment variables or a `.env` file:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: false)
- `APP_NAME`: Application name
- `APP_VERSION`: Application version

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.