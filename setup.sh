#!/bin/bash

# Keyword Management System - Development Setup Script

echo "🚀 Setting up Keyword Management System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose (try both old and new syntax)
if ! (command -v docker-compose &> /dev/null || docker compose version &> /dev/null); then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

# Use docker compose (new syntax) if available, otherwise docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Create data directory for SQLite
mkdir -p backend/data

echo "📦 Building and starting services with Docker Compose..."
$DOCKER_COMPOSE up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check if API is healthy
echo "🔍 Checking API health..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ API is running at http://localhost:8000"
    echo "📚 API Documentation available at http://localhost:8000/docs"
else
    echo "❌ API is not responding. Check logs with: $DOCKER_COMPOSE logs"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Available commands:"
echo "  $DOCKER_COMPOSE up -d          # Start services"
echo "  $DOCKER_COMPOSE down           # Stop services"
echo "  $DOCKER_COMPOSE logs -f        # View logs"
echo "  $DOCKER_COMPOSE restart        # Restart services"
echo ""
echo "🔗 Access points:"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"