# Asynchronous Web Crawler and Semantic Search Engine

This project is a powerful and scalable web crawling system designed to fetch, process, and index web content for semantic search. It uses an asynchronous, message-driven architecture with RabbitMQ and Scrapy for crawling.

## Features

*   **Asynchronous Crawling**: Utilizes RabbitMQ to manage crawling jobs, allowing for non-blocking operations and easy scalability.
*   **Scrapy-based Crawling**: Uses the powerful and flexible Scrapy framework for web crawling.
*   **Semantic Search**: Leverages vector embeddings (via `pgvector`) to provide intelligent, meaning-based search over the crawled data.
*   **Modern Frontend**: A Next.js and Shadcn UI-based frontend provides a user-friendly interface to manage and monitor crawling jobs.
*   **Dockerized Infrastructure**: Core dependencies like PostgreSQL, RabbitMQ, and Ollama are managed with Docker, ensuring a consistent and easy-to-set-up environment.
*   **Database Migrations**: Uses Alembic to manage database schema changes in a structured and version-controlled way.
*   **RESTful API**: A Flask-based API provides endpoints to start, stop, and monitor crawlers, as well as perform searches.

## Frontend

The frontend is a Next.js application that provides a user-friendly interface for interacting with the crawler system.

### Current Features

*   **Dashboard**: View analytics such as total domains, total URLs, running crawlers, and completed jobs.
*   **Jobs Management**: View a list of all crawling jobs, create new jobs, and stop or delete existing jobs.
*   **Web Pages**: View a list of all crawled web pages with pagination and search functionality.

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
└── frontend/
    ├── package.json
    ├── next.config.ts
    └── src/
        ├── app/
        ├── components/
        └── services/
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

#### Backend

Start the Flask application.

```bash
conda run -n crawler python backend/src/app.py
```

The backend will be running at `http://localhost:5000`.

#### Frontend

In a separate terminal, start the Next.js frontend.

```bash
cd frontend
npm install
npm run dev
```

The frontend will be running at `http://localhost:3000`.

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
    *   **Body (JSON)**: `{ "domain": "https://example.com", "depth": 2 }`
*   `POST /stop-crawler/<job_id>`: Stops a running crawler.
*   `GET /crawler-status/<job_id>`: Gets the status of a specific job.
*   `GET /crawlers-status`: Gets the status of all jobs.
*   `POST /search`: Performs a semantic search on the crawled data.
    *   **Body (JSON)**: `{ "query": "your search query", "limit": 5 }`
*   `GET /api/jobs`: Get a list of all jobs.
*   `GET /api/jobs/<job_id>`: Get a specific job by ID.
*   `PUT /api/jobs/<job_id>`: Update a job.
*   `DELETE /api/jobs/<job_id>`: Delete a job.

## Debugging

Here are some common issues and how to resolve them:

### RabbitMQ Issues

*   **Check the logs**: Use `docker logs <rabbitmq-container-name>` to check for any errors.
*   **Memory allocation**: Ensure that the RabbitMQ container has enough memory allocated to it.
*   **Authentication**: Verify that the username and password in your `.env` file match the credentials configured in `docker-compose.yml`.

### Database Errors

*   **Migrations not run**: Ensure that you have run `npm run db:up` after any changes to the database models.
*   **Database corruption**: If you suspect the database is in a bad state, you can reset it by running:
    ```bash
    npm run docker:down
    # Remove the postgres volume to delete all data
    docker volume rm <project-name>_postgres_data
    npm run docker:up
    npm run db:up
    ```

### Ollama and Llama Issues

*   **Check Ollama logs**: Use `docker logs <ollama-container-name>` to see if the service is running correctly.
*   **Model not pulled**: Ensure that the `llama3.2:latest` model has been pulled correctly by Ollama. You can check the logs for messages related to model pulling.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1.  **Fork the repository**.
2.  **Create a new branch**: `git checkout -b my-feature-branch`
3.  **Make your changes**: Ensure that you follow the existing coding standards and write clean, well-documented code.
4.  **Commit your changes**: `git commit -m "Add some feature"`
5.  **Push to the branch**: `git push origin my-feature-branch`
6.  **Create a new Pull Request**.
