# Asynchronous Web Crawler and Semantic Search Engine

This project is a powerful and scalable web crawling system designed to fetch, process, and index web content for semantic search. It uses an asynchronous, message-driven architecture with RabbitMQ and offers multiple crawling strategies, including Scrapy and Selenium.

## Features

*   **Asynchronous Crawling**: Utilizes RabbitMQ to manage crawling jobs, allowing for non-blocking operations and easy scalability.
*   **Multiple Crawler Implementations**: Switch between different crawling backends (`Scrapy`, `Selenium`, custom APIs) via a simple configuration change.
*   **Semantic Search**: Leverages vector embeddings (via `pgvector`) to provide intelligent, meaning-based search over the crawled data.
*   **Dockerized Infrastructure**: Core dependencies like PostgreSQL, RabbitMQ, and Ollama are managed with Docker, ensuring a consistent and easy-to-set-up environment.
*   **Database Migrations**: Uses Alembic to manage database schema changes in a structured and version-controlled way.
*   **RESTful API**: A Flask-based API provides endpoints to start, stop, and monitor crawlers, as well as perform searches.

## Directory Structure

```
.
├── alembic.ini
├── docker-compose.yml
├── package.json
├── backend
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic/
│   └── src/
│       ├── app.py
│       ├── models.py
│       └── ...
└── ...
```

## How to Run Locally

### Prerequisites

*   [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
*   [Node.js and npm](https://nodejs.org/en/download/)
*   [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) (for managing the Python environment)

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

The default values are configured to work with the `docker-compose.yml` file.

### 3. Set Up Python Environment

This project uses a Conda environment to manage Python dependencies.

```bash
# Create and activate the conda environment
conda create -n crawler python=3.10 -y
conda activate crawler

# Install the required python packages
pip install -r backend/requirements.txt
```

### 4. Start Services and Run Migrations

These commands will start the Docker containers and then apply the database migrations.

```bash
# Start Docker containers (Postgres, RabbitMQ, Ollama)
npm run docker:up

# Apply database migrations
npm run db:up
```

### 5. Run the Application

Finally, start the Flask application.

```bash
conda run -n crawler python backend/src/app.py
```

The application will be running at `http://localhost:5000`.

## Database Migrations

This project uses Alembic to handle database schema migrations.

### Creating a New Migration

When you make changes to the SQLAlchemy models in `backend/src/models.py`, you'll need to generate a new migration script.

1.  **Generate the migration script**:
    ```bash
    npm run db:new-migration -- -m "Your descriptive migration message"
    ```
    *Note the `--` which is required to pass arguments to the underlying script.*

2.  **Review the script**: A new file will be created in `backend/alembic/versions/`. Open this file and review the generated code to ensure it's correct.

3.  **Apply the migration**:
    ```bash
    npm run db:up
    ```

### Downgrading a Migration

To revert the last migration, use the `db:down` command:

```bash
npm run db:down
```

## API Endpoints

The main API endpoints are defined in `backend/src/app.py`.

*   `POST /start-crawler`: Starts a new crawling job.
    *   **Body (JSON)**: `{ "url": "https://example.com", "depth": 2 }`
*   `POST /stop-crawler/<job_id>`: Stops a running crawler.
*   `GET /crawler-status/<job_id>`: Gets the status of a specific job.
*   `GET /crawlers-status`: Gets the status of all jobs.
*   `POST /search`: Performs a semantic search on the crawled data.
    *   **Body (JSON)**: `{ "query": "your search query", "limit": 5 }`
