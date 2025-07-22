# Asynchronous Web Crawler and Semantic Search Engine

This project is a powerful and scalable web crawling system designed to fetch, process, and index web content for semantic search. It uses an asynchronous, message-driven architecture with RabbitMQ and offers multiple crawling strategies, including Scrapy and Selenium.

## Features

*   **Asynchronous Crawling**: Utilizes RabbitMQ to manage crawling jobs, allowing for non-blocking operations and easy scalability.
*   **Multiple Crawler Implementations**: Switch between different crawling backends (`Scrapy`, `Selenium`, custom APIs) via a simple configuration change.
*   **Semantic Search**: Leverages vector embeddings (via `pgvector`) to provide intelligent, meaning-based search over the crawled data.
*   **Dockerized Infrastructure**: Core dependencies like PostgreSQL and RabbitMQ are managed with Docker, ensuring a consistent and easy-to-set-up environment.
*   **RESTful API**: A Flask-based API provides endpoints to start, stop, and monitor crawlers, as well as perform searches.

## Architecture Overview

The system is composed of several key components:

*   **API & Orchestration (`backend/src/app.py`)**: A Flask application that exposes a REST API for managing the system. It handles incoming requests and publishes events to RabbitMQ.
*   **Asynchronous Messaging (`backend/src/rabbitmq_events.py`)**: RabbitMQ is used as a message broker to decouple the API from the crawlers. This allows for resilient and scalable job processing.
*   **Crawler Abstraction (`backend/src/crawlers/`)**: A factory pattern is used to create and manage different types of crawlers. This makes the system extensible and allows for choosing the best tool for a given website.
    *   **Implementations**: Includes `Scrapy` for fast, efficient crawling and `Selenium` for dynamic, JavaScript-heavy sites.
*   **Event Handlers (`backend/src/crawlers/crawler_event_handlers.py`)**: These are the consumers of the RabbitMQ messages. They listen for events (e.g., `START_CRAWLER`) and execute the corresponding crawling jobs.
*   **Data Persistence (`backend/src/db.py`)**: A PostgreSQL database with the `pgvector` extension is used to store crawled data and their vector embeddings.
*   **Search (`backend/src/search.py`, `backend/src/embeddings.py`)**: This component is responsible for generating vector embeddings from the crawled content and providing a search interface to find semantically similar results.

## Directory Structure

```
.
├── docker-compose.yml
├── backend
│   ├── .env.example
│   └── src
│       ├── app.py                 # Flask API and main application entry point
│       ├── db.py                  # Database connection and operations
│       ├── embeddings.py          # Vector embedding generation
│       ├── rabbitmq_events.py     # RabbitMQ event publishing and handling
│       ├── search.py              # Semantic search logic
│       └── crawlers
│           ├── crawler_factory.py # Factory for creating crawlers
│           ├── interface.py       # Common interface for all crawlers
│           └── implementations
│               ├── scrapy_crawler.py
│               └── selenium_crawler.py
└── ...
```

## How to Run Locally

### Prerequisites

*   [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
*   [Python 3.8+](https://www.python.org/downloads/) and `pip`

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up Environment Variables

Create a `.env` file in the `backend/` directory by copying the example file.

```bash
cp backend/.env.example backend/.env
```

Modify the `backend/.env` file as needed. The default values are configured to work with the `docker-compose.yml` file.

### 3. Start Infrastructure Services

This command will start the PostgreSQL database and RabbitMQ message broker in the background.

```bash
docker-compose up -d
```

You can check the status of the containers with `docker-compose ps`.

### 4. Install Python Dependencies

Navigate to the `backend` directory and install the required Python packages using the `requirements.txt` file.

```bash
pip install -r backend/requirements.txt
```

### 5. Run the Application

Once the dependencies are installed, you can start the Flask application.

```bash
python backend/src/app.py
```

The application will be running at `http://localhost:5000`.

## API Endpoints

The main API endpoints are defined in `backend/src/app.py`.

*   `POST /start-crawler`: Starts a new crawling job.
    *   **Body (JSON)**: `{ "url": "https://example.com", "depth": 2 }`
*   `POST /stop-crawler/<job_id>`: Stops a running crawler.
*   `GET /crawler-status/<job_id>`: Gets the status of a specific job.
*   `GET /crawlers-status`: Gets the status of all jobs.
*   `POST /search`: Performs a semantic search on the crawled data.
    *   **Body (JSON)**: `{ "query": "your search query", "limit": 5 }`
