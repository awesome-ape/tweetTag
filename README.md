# tweetTag
# TweetTag

TweetTag is a full-stack web application designed for collecting, reviewing, and labeling social-media posts related to energy infrastructure.

The platform provides a structured annotation workflow in which users analyze tweets, assign labels, and contribute to building high-quality labeled datasets for downstream machine-learning tasks.

## Features

* **Tweet Collection** – Integrates with Apify to collect social-media posts for analysis.
* **Structured Annotation Workflow** – Users review tweets and assign labels through an interactive interface.
* **Multi-stage Tagging** – Supports different tagging tasks and classification workflows.
* **User Authentication** – Secure registration and login using JWT-based authentication.
* **Password Recovery** – Email-based password reset flow.
* **User & Admin Management** – Separate functionality for regular users and administrators.
* **Task Locking** – Prevents multiple users from simultaneously working on the same task.
* **Task Timeouts** – Handles inactive annotation sessions and releases locked tasks.
* **Escalation Workflow** – Supports cases that require additional review.
* **Statistics & Insights** – Tracks annotation activity and platform usage.
* **Leaderboard** – Displays user contribution statistics.

## Tech Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* Python
* FastAPI
* Pydantic
* JWT Authentication

### Database

* MongoDB
* Motor

### External Services

* Apify
* SMTP Email Service

## Architecture

TweetTag follows a client-server architecture:

```text
React / Vite Frontend
        |
        | HTTP / REST
        v
FastAPI Backend
        |
        +---- Authentication & User Management
        |
        +---- Tweet & Annotation Services
        |
        +---- Task Management
        |
        +---- Statistics & Insights
        |
        v
     MongoDB

        +
        |
        +---- Apify
        +---- Email Service
```

The backend is organized into separate controllers, services, schemas, dependencies, and database layers to keep the application's responsibilities separated.

## Project Structure

```text
tweetTag/
├── backend/
│   └── app/
│       ├── controller/
│       ├── core/
│       ├── db/
│       ├── dependencies/
│       ├── schemas/
│       ├── services/
│       │   ├── tweets/
│       │   └── users/
│       └── scripts/
│
└── frontend/
    └── src/
```

## Authentication

TweetTag uses JWT-based authentication to protect authenticated endpoints.

The authentication system includes:

* User registration
* Login
* Password hashing
* JWT access tokens
* Protected API endpoints
* Email-based password recovery

Sensitive configuration such as API tokens and database credentials should be provided through environment variables and must not be committed to the repository.

## Annotation Workflow

A typical workflow consists of:

1. A user authenticates to the platform.
2. The user receives an available annotation task.
3. The task is temporarily locked to prevent concurrent editing.
4. Tweets are displayed through the web interface.
5. The user assigns the appropriate labels.
6. The annotations are submitted to the backend.
7. The results are stored in MongoDB.
8. Statistics and user contribution data are updated.

Tasks that cannot be confidently classified can be escalated for additional review.

## Running the Project

### Backend

Navigate to the backend directory and install the required Python dependencies.

```bash
pip install -r requirements.txt
```

Configure the required environment variables and start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

### Frontend

Navigate to the frontend directory:

```bash
npm install
npm run dev
```

The Vite development server will then start the frontend application.

## Environment Variables

The application uses environment variables to manage sensitive configuration.

Create a `.env` file and configure the required variables:

```env
MONGO_URI=your_mongodb_connection_string
APIFY_API_TOKEN=your_apify_api_token
SECRET_KEY=your_jwt_secret_key
```

> **Security:** Never commit your `.env` file or real credentials to the repository.


## Purpose

TweetTag was built as a practical full-stack system combining web development, data collection, authentication, database management, and collaborative data annotation.

The project focuses on creating a usable workflow for turning raw social-media data into structured labeled data that can later support machine-learning applications.

## Future Improvements

* Automated ML-assisted labeling
* More detailed annotation analytics
* Improved conflict-resolution workflows
* Expanded testing coverage
* Deployment and monitoring improvements

## Authors

**Almog Salman** — Computer Science Student
**Yuval Cohen** — Computer Science Student
