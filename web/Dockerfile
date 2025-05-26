# Base image for development dependencies
FROM oven/bun:1 AS base

# No need for pnpm installation since we'll use bun

# Install common dependencies that are likely to be used in Next.js projects
FROM base AS deps
WORKDIR /app

# Copy only package files for efficient caching
COPY . .

# Install dependencies
RUN bun install

# Install git and configure it
RUN apt-get update -y && apt-get install -y git && \
    cd /app && \
    git init && \
    git config --system --add safe.directory /app && \
    git config --system user.name "creatr-agent" && \
    git config --system user.email "creatr-agent@getcreatr.com" && \
    git add . && \
    git commit -m "Initial Commit"

# Create a separate stage for exporting
FROM alpine:latest AS export-stage

# Create tar archive of the source code (excluding node_modules)
COPY --from=deps /app /source
RUN cd /source && \
    tar -czf /source.tar.gz --exclude=node_modules .

# Copy node_modules to a separate location for volume mounting
COPY --from=deps /app/node_modules /deps/node_modules

# Clean up the source directory and extract the tar
RUN rm -rf /source/* && \
    mv /source.tar.gz /source/