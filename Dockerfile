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
# Handle persistent data directory\n\
echo "Checking persistent data directory..."\n\
\n\
# Initialize empty files only if they dont exist (preserve existing data)\n\
for file in trading_decisions.json thought_processes.json chat_sessions.json equity_snapshots.json pending_actions.json positions.json profile_updates.json trading_data.json chat_influence_results.json; do\n\
    if [ ! -f /data/$file ]; then\n\
        echo "{}" > /data/$file\n\
        echo "Created empty $file"\n\
    fi\n\
done\n\
\n\
# Special handling for accounts.json\n\
if [ ! -f /data/accounts.json ]; then\n\
    echo "No accounts.json found in persistent storage"\n\
    if [ -f /app/data/accounts_deployment.json ]; then\n\
        echo "Using deployment accounts (4 personas)"\n\
        cp /app/data/accounts_deployment.json /data/accounts.json\n\
    else\n\
        echo "{}" > /data/accounts.json\n\
    fi\n\
else\n\
    echo "Using existing accounts.json from persistent storage"\n\
    # Check if we need to update personas (deployment flag)\n\
    if [ "$RESET_PERSONAS" = "true" ] && [ -f /app/data/accounts_deployment.json ]; then\n\
        echo "RESET_PERSONAS=true - Replacing with deployment accounts"\n\
        cp /data/accounts.json /data/accounts_backup_$(date +%s).json\n\
        cp /app/data/accounts_deployment.json /data/accounts.json\n\
    fi\n\
fi\n\
\n\
# Markets data - always use latest if available\n\
if [ -f /app/data/markets.json ]; then\n\
    cp /app/data/markets.json /data/\n\
    echo "Updated markets.json with latest data"\n\
elif [ ! -f /data/markets.json ]; then\n\
    echo "{}" > /data/markets.json\n\
fi\n\
\n\
# Start the application\n\
exec python start_bot.py' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]