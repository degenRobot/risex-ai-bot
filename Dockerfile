FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1

WORKDIR /app

# Install poetry
RUN pip install poetry==${POETRY_VERSION}

# Configure poetry
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Copy initial data files (only if /data is empty)
RUN mkdir -p /app/initial_data
# Note: COPY doesn't support wildcards with empty source, handled in entrypoint

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Create entrypoint script to handle data initialization
RUN echo '#!/bin/bash\n\
# Initialize data directory structure\n\
if [ ! -f /data/accounts.json ]; then\n\
    echo "Initializing empty data directory..."\n\
    echo "{}" > /data/accounts.json\n\
    echo "{}" > /data/trading_decisions.json\n\
    echo "{}" > /data/thought_processes.json\n\
    echo "{}" > /data/chat_sessions.json\n\
    echo "{}" > /data/equity_snapshots.json\n\
    echo "{}" > /data/pending_actions.json\n\
    echo "{}" > /data/positions.json\n\
    echo "{}" > /data/profile_updates.json\n\
    echo "{}" > /data/trading_data.json\n\
    echo "{}" > /data/chat_influence_results.json\n\
    # Copy markets.json if it exists in app directory\n\
    if [ -f /app/data/markets.json ]; then\n\
        cp /app/data/markets.json /data/\n\
    else\n\
        echo "{}" > /data/markets.json\n\
    fi\n\
    echo "Data initialization complete."\n\
else\n\
    echo "Data directory already initialized, skipping."\n\
fi\n\
\n\
# Start the application\n\
exec python start_bot.py' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]