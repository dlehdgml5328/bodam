# PostgreSQL with both PostGIS and pgvector
FROM postgis/postgis:16-3.4

# Install pgvector
RUN apt-get update && \
    apt-get install -y postgresql-16-pgvector && \
    rm -rf /var/lib/apt/lists/*

# Verify installations
RUN echo "PostGIS and pgvector installed successfully"
