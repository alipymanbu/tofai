# TOF.ai

TOF.ai is an AI-powered video generation platform for brand awareness. The platform guides users through a brand strategy framework with multiple choice options, then uses AI to generate scripts, visuals/images, speech and music before finally combining everything into a social media video.

## Tech Stack

### Core Technologies
- **Backend**: FastAPI
- **Database**: MongoDB for persistent storage
- **Caching**: Redis for session/job caching and message brokering
- **Task Queue**: Celery for asynchronous processing
- **Object Storage**: S3-compatible storage for media files

### AI Components
- **AI Orchestration**: LangGraph for workflow orchestration
- **LLM Support**: 
  - Google Gemini API
  - ElevenLabs for Text-to-Speech
- **Agent Framework**: Langchain for tool-enabled agents
- **Authentication**: AWS Cognito for user authentication

## Architecture Overview

```mermaid
graph TD
    User[User/Client] --> API[FastAPI Backend]
    API --> DB[(MongoDB)]
    API --> Redis[(Redis)]
    API --> S3[(S3 Storage)]
    API --> AI[AI Services]
    API --> Celery[Celery Worker]
    
    AI --> LMFacade[LM Facade]
    LMFacade --> Gemini[Google Gemini API]
    LMFacade --> ElevenLabs[ElevenLabs TTS]
    
    Celery --> Redis
    Celery --> AI
    
    subgraph Content Generation
        AI --> FrameworkGen[Framework Generator]
        AI --> VideoCreation[Video Creation]
        AI --> TextToImage[Text-to-Image]
        AI --> TextToSpeech[Text-to-Speech]
    end
    
    VideoCreation --> S3
    TextToImage --> S3
    TextToSpeech --> S3
```

## Environment Setup

The application uses environment variables for configuration. These are managed through a `.env` file in the project root directory.

### Local Development Setup

1. Create your `.env` file from the template:
   ```bash
   ./scripts/create-env-file.sh
   ```

2. Edit the `.env` file with your actual configuration values:
   ```bash
   # Use your preferred text editor
   nano .env
   ```

3. The `.env` file is automatically loaded by the application at startup, and it's excluded from version control for security.

### Environment Variables

Key environment variables include:

- **MongoDB**: `MONGODB_URI`, `DATABASE_NAME`
- **Redis**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_USER`, `REDIS_SECRET`
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- **S3**: `S3_BUCKET`, `S3_REGION`
- **AI Services**: `GEMINI_API_PROJECT_NUMBER`, `GEMINI_API_SECRET`, `ELEVEN_TTS_SECRET`
- **Google Search**: `GOOGLE_SEARCH_API_KEY`, `GOOGLE_CSE_ID`
- **Cognito**: `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, etc.

### Kubernetes Deployment

For Kubernetes deployment, the environment variables are managed as Kubernetes secrets:

1. Set all required environment variables in your shell 
2. Generate the Kubernetes secrets file:
   ```bash
   ./scripts/generate-k8s-secrets.sh
   ```
3. Apply the secrets to your cluster:
   ```bash
   kubectl apply -f k8s/secrets.yaml
   ```

## API Endpoints

### Authentication
- **Login**: `GET /api/auth/login`
  - Description: Redirects to Cognito login page
  - Query Parameters: 
    - `state` (Optional): String to be returned after authentication

- **Logout**: `GET /api/auth/logout`
  - Description: Logs out the user and clears session cookies

- **Callback**: `GET /api/auth/callback`
  - Description: Handler for Cognito authentication callback
  - Query Parameters:
    - `code`: Authorization code from Cognito
    - `state` (Optional): State string passed during login

- **Get Current User**: `GET /api/auth/user`
  - Description: Returns the current authenticated user's information
  - Response Model:
    ```json
    {
      "id": "string",
      "username": "string",
      "email": "string",
      "cognito:groups": ["string"]
    }
    ```

### Session Management
- **Create Session**: `POST /api/sessions`
  - Description: Creates a new user session
  - Authentication: Required
  - Response Model:
    ```json
    {
      "id": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "status": "integer",
      "result": "object",
      "framework_id": "string",
      "current_step_id": "string"
    }
    ```

- **Get Session**: `GET /api/sessions/{session_id}`
  - Description: Get details of a specific session
  - Path Parameters:
    - `session_id`: Session ID
  - Authentication: Required
  - Response: Session object

- **Delete Session**: `DELETE /api/sessions/{session_id}`
  - Description: Delete a session
  - Path Parameters:
    - `session_id`: Session ID
  - Authentication: Required
  - Response: 204 No Content

- **List User Sessions**: `GET /api/sessions/user/me`
  - Description: Get all sessions for the current user
  - Authentication: Required
  - Response: Array of Session objects

### Framework Generation
- **Initial Input**: `POST /api/framework/steps/initial_input`
  - Description: Submit initial brand information
  - Query Parameters:
    - `session_id`: Session ID to update
  - Request Body:
    ```json
    {
      "framework_id": "string",
      "brand_link": "string"
    }
    ```
  - Authentication: Required
  - Response:
    ```json
    {
      "job_id": "string",
      "created_at": "datetime",
      "framework_id": "string"
    }
    ```

- **Generate Options**: `POST /api/framework/steps/{step_id}/generate`
  - Description: Generate options for a specific framework step
  - Path Parameters:
    - `step_id`: Framework step ID
  - Query Parameters:
    - `session_id`: Session ID to update
  - Request Body:
    ```json
    {
      "framework_id": "string",
      "step_id": "string"
    }
    ```
  - Authentication: Required
  - Response:
    ```json
    {
      "message": "string",
      "job_id": "string",
      "status": "string",
      "progress": "integer"
    }
    ```

- **Select Option**: `POST /api/framework/steps/{step_id}/select`
  - Description: Select an option for a framework step
  - Path Parameters:
    - `step_id`: Framework step ID
  - Query Parameters:
    - `session_id`: Session ID to update
    - `option_index`: Index of the selected option
    - `result_index`: Index of the result group to select from (default: 0)
  - Request Body:
    ```json
    {
      "framework_id": "string"
    }
    ```
  - Authentication: Required
  - Response:
    ```json
    {
      "job_id": "string",
      "created_at": "datetime",
      "framework_id": "string"
    }
    ```

### Jobs
- **Get Job Status**: `GET /api/jobs/{job_id}`
  - Description: Check the status of an asynchronous job
  - Path Parameters:
    - `job_id`: Job ID
  - Authentication: Required
  - Response:
    ```json
    {
      "id": "string",
      "session_id": "string",
      "created_at": "datetime",
      "completed_at": "datetime",
      "status": "string",
      "progress": "integer",
      "tasks_completed": ["string"],
      "error": "string"
    }
    ```

### Health
- **Health Check**: `GET /api/health`
  - Description: API health check endpoint
  - Response:
    ```json
    {
      "status": "string",
      "environment": "string",
      "database_initialized": "boolean"
    }
    ```

## Data Models

### User
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### SessionStatus (Enum)
```
UNDEFINED = 0
STARTED = 1
EXPIRED = 2
```

### Session
```json
{
  "id": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "expired_at": "datetime",
  "status": "SessionStatus",
  "result": "FrameworkResult",
  "framework_id": "string",
  "current_step_id": "string"
}
```

### JobStatus (Enum)
```
UNDEFINED = 0
PENDING = 1
PROCESSING = 2
COMPLETED = 3
FAILED = 4
CANCELED = 5
```

### Job
```json
{
  "id": "string",
  "session_id": "string",
  "created_at": "datetime",
  "completed_at": "datetime",
  "status": "JobStatus",
  "progress": "integer",
  "tasks_completed": ["string"],
  "error": "string"
}
```

### Framework Models
```json
{
  "FrameworkResult": {
    "id": "string",
    "step_results": ["FrameworkStepResult"]
  },
  
  "FrameworkStepResult": {
    "id": "string",
    "result": ["ResultOptions"]
  },
  
  "ResultOptions": {
    "result_options": ["string or MediaUri"],
    "selected_option": "integer"
  },
  
  "MediaUri": {
    "uri": "string"
  }
}
```
