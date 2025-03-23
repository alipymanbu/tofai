# TOF.ai

TOF.ai is an AI-powered video generation platform for brand awareness. The platform guides users through a brand strategy with multiple choice options, then uses AI to generate script, visuals/images, speech and music before finally combining everything into a social media video.

## Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB (storage) and Redis (caching)
- **Task Queue**: Celery
- **AI Orchestration**: LangGraph
- **Object Storage**: S3-compatible storage (AWS S3, MinIO, etc.)

## Features

- Brand strategy framework development
- AI-generated content scripts
- AI-generated visuals
- Text-to-speech voiceovers
- Background music generation
- Video compilation
- End-to-end workflow orchestration

## Local Development Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tof-agent.git
   cd tof-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the MongoDB and Redis services using Docker Compose:
   ```bash
   docker-compose up -d mongo redis
   ```

5. Run the application locally:
   ```bash
   uvicorn main:app --reload
   ```

6. The API will be available at http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Server
PORT=8000
DEBUG=True
ENVIRONMENT=development

# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=tofai

# Redis
REDIS_URI=redis://localhost:6379/0

# AI Services
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Storage
S3_BUCKET=tofai-media
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

## API Endpoints

- **Sessions**: `/api/sessions`
- **Brand Strategy**: `/api/sessions/{session_id}/strategy`
- **Script Generation**: `/api/sessions/{session_id}/script`
- **Image Generation**: `/api/sessions/{session_id}/image`
- **Speech Generation**: `/api/sessions/{session_id}/speech`
- **Music Generation**: `/api/sessions/{session_id}/music`
- **Video Generation**: `/api/sessions/{session_id}/video`
- **Jobs**: `/api/jobs`

## Project Structure

```
tof-agent/
├── api/                     # API routes and endpoints
│   ├── routes/              # API route modules
│   └── celery_worker.py     # Celery worker configuration
├── config/                  # Configuration
│   └── settings.py          # App settings
├── models/                  # Data models
│   ├── base.py              # Base models
│   └── session.py           # Session models
├── services/                # Business logic
│   ├── ai/                  # AI generation services
│   │   ├── tasks/           # AI tasks
│   │   ├── ai_orchestrator.py  # AI orchestration
│   │   ├── lm_facade.py     # Language model wrapper
│   │   └── state.py         # State management
│   └── storage/             # Storage services
│       ├── database.py      # Database access
│       └── object_store.py  # Object storage (S3)
├── main.py                  # Application entry point
├── Dockerfile               # Docker definition
├── docker-compose.yml       # Docker Compose services
└── requirements.txt         # Python dependencies
```

## Running with Docker

To run the entire application stack with Docker:

```bash
docker-compose up -d
```

## Running Tasks with Celery

Start the Celery worker:

```bash
celery -A api.celery_worker worker --loglevel=info
```
