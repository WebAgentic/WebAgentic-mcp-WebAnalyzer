#!/bin/bash

# Web Analyzer MCP Server Deployment Script

set -e

echo "🚀 Deploying Web Analyzer MCP Server..."

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f .env ]]; then
        print_warning ".env file not found, using .env.example"
        cp .env.example .env
        print_warning "Please update .env with your configuration"
    fi
    
    print_status "Prerequisites check completed"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    docker build -t web-analyzer-mcp:${IMAGE_TAG} .
    
    if [[ -n "${DOCKER_REGISTRY}" && "${DOCKER_REGISTRY}" != "localhost:5000" ]]; then
        docker tag web-analyzer-mcp:${IMAGE_TAG} ${DOCKER_REGISTRY}/web-analyzer-mcp:${IMAGE_TAG}
        docker push ${DOCKER_REGISTRY}/web-analyzer-mcp:${IMAGE_TAG}
    fi
    
    print_status "Docker image built successfully"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✅ API server is healthy"
    else
        print_error "❌ API server health check failed"
        exit 1
    fi
    
    print_status "Deployment completed successfully"
    print_status "🌐 API Server: http://localhost:8000"
    print_status "📊 Flower (Celery Monitor): http://localhost:5555"
    print_status "📈 Metrics: http://localhost:9090/metrics"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Create namespace
    kubectl apply -f deployment/kubernetes/namespace.yaml
    
    # Apply configurations
    kubectl apply -f deployment/kubernetes/configmap.yaml
    
    # Deploy Redis
    kubectl apply -f deployment/kubernetes/redis.yaml
    
    # Wait for Redis to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n web-analyzer
    
    # Deploy API server and workers
    kubectl apply -f deployment/kubernetes/api-server.yaml
    kubectl apply -f deployment/kubernetes/worker.yaml
    
    # Wait for deployments
    kubectl wait --for=condition=available --timeout=300s deployment/web-analyzer-api -n web-analyzer
    kubectl wait --for=condition=available --timeout=300s deployment/web-analyzer-worker -n web-analyzer
    
    # Apply ingress (optional)
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        kubectl apply -f deployment/kubernetes/ingress.yaml
    fi
    
    print_status "Kubernetes deployment completed"
    
    # Show status
    kubectl get pods -n web-analyzer
}

# Main deployment logic
main() {
    case "${1:-docker}" in
        "docker"|"compose")
            check_prerequisites
            build_image
            deploy_docker_compose
            ;;
        "k8s"|"kubernetes")
            check_prerequisites
            build_image
            deploy_kubernetes
            ;;
        "build-only")
            check_prerequisites
            build_image
            ;;
        *)
            echo "Usage: $0 [docker|kubernetes|build-only]"
            echo "  docker     - Deploy using Docker Compose (default)"
            echo "  kubernetes - Deploy to Kubernetes cluster"
            echo "  build-only - Only build the Docker image"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"