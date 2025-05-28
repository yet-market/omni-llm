# Claude Code Instructions for Enterprise AI Gateway

## Project Context
Enterprise-Grade Multi-Provider AI Gateway with Distributed Computing Architecture and Intelligent Load Balancing on AWS Serverless Infrastructure. This is a sophisticated cloud-native solution featuring containerized microservices architecture, ECR-based deployment pipelines, intelligent provider orchestration, and advanced distributed computing capabilities.

## Development Guidelines

### Code Style
- Use Python 3.11+ with comprehensive type hints
- Follow PEP 8 style guidelines with enterprise conventions
- Use async/await for I/O operations and concurrent processing
- Implement comprehensive error handling with structured logging
- Add detailed docstrings for all public functions and classes

### Architecture Patterns
- Use dependency injection for provider orchestration
- Implement abstract base classes for extensible architecture
- Use Pydantic models for enterprise data validation
- Follow the repository pattern for data access layers
- Implement proper separation of concerns across modules

### Testing Requirements
- Maintain >95% test coverage for enterprise quality
- Use pytest with advanced fixtures and parameterization
- Mock external API calls and container dependencies
- Test both success and failure scenarios comprehensively
- Include integration tests for ECR deployment pipeline

### Security Considerations
- Never log sensitive data (API keys, tokens, PII)
- Validate all inputs using Pydantic with strict schemas
- Use AWS IAM roles for service authentication
- Implement proper error handling without data leakage
- Follow least privilege principle across all AWS resources

### Performance Optimization
- Optimize for Lambda container cold start times
- Use connection pooling for external API calls
- Implement intelligent caching strategies across layers
- Monitor and optimize memory usage patterns
- Leverage ARM64 architecture for cost and performance benefits

### Container Architecture

#### ECR Repository Management
- **Private Registry**: All images stored in AWS ECR private repositories
- **Vulnerability Scanning**: Automatic security scanning on image push
- **Lifecycle Policies**: Automated cleanup of old images (keep last 10)
- **Multi-environment**: Separate repositories for staging/production

#### Docker Optimization
- **Multi-stage Builds**: Optimize layer caching for fast rebuilds
- **ARM64 Native**: Build specifically for AWS Graviton2 processors
- **Minimal Base**: Use official AWS Lambda Python runtime
- **Dependency Layering**: Strategic COPY ordering for cache efficiency

### Deployment Architecture

#### Branch Strategy
- **`staging` branch**: Development and testing environment
- **`master` branch**: Production-ready stable releases

#### Environment-Specific Deployment
- **Staging**: `./deployment/scripts/deploy.sh staging`
  - ECR repository: `omni-llm-gateway-staging`
  - 1024MB container memory
  - 100 req/s API throttling
  - Development-optimized configuration

- **Production**: `./deployment/scripts/deploy.sh prod`
  - ECR repository: `omni-llm-gateway-prod`
  - 2048MB container memory
  - 1000 req/s API throttling
  - Enterprise security and monitoring

#### Container Deployment Workflow
1. **Docker Build**: Multi-stage optimized container build
2. **ECR Authentication**: AWS CLI login to private registry
3. **Image Push**: Tagged images to environment-specific repository
4. **Lambda Update**: Function code updated with new container image
5. **Health Verification**: Automated deployment testing

#### Pre-Deployment Checklist
- Test containerized application locally
- Run linting and type checking: `python -m pylint src/ && python -m mypy src/`
- Run comprehensive tests: `python -m pytest tests/ -v --cov=src`
- Ensure .env file is configured for staging deployments
- Verify ECR repository permissions and access

#### Deployment Commands
```bash
# Staging deployment with ECR
./deployment/scripts/deploy.sh staging

# Production deployment with ECR
./deployment/scripts/deploy.sh prod

# Container health check
curl https://your-api-gateway-url/health
```

### File Organization
- Keep modules focused and cohesive with clear boundaries
- Use the established enterprise project structure
- Add new providers in `src/providers/` with proper abstraction
- Add new vector stores in `src/rag/vector_stores/` following patterns
- Update configuration models when adding enterprise features

### AWS Infrastructure Components

#### Core Services
1. **ECR Repository**: Container image registry with scanning
2. **Lambda Function**: ARM64 container runtime with auto-scaling
3. **API Gateway**: Regional endpoints with enterprise authentication
4. **CloudWatch**: Comprehensive logging and monitoring
5. **X-Ray**: Distributed tracing for performance analysis
6. **IAM**: Least-privilege security model

#### Security & Compliance
1. **Container Scanning**: Vulnerability assessment on each push
2. **Environment Isolation**: Separate ECR repos for staging/prod
3. **API Authentication**: Key-based access with usage plans
4. **Audit Logging**: Complete request/response tracking
5. **Encryption**: At-rest and in-transit data protection

## Key Components to Remember

1. **Container-First Architecture**: Everything deployed as optimized containers
2. **ECR Integration**: Private registry with automated lifecycle management
3. **Multi-Provider Orchestration**: LangChain native fallback chains
4. **Enterprise Security**: Comprehensive IAM and encryption
5. **Performance Engineering**: ARM64 optimization and caching strategies

## Development Workflow

### Local Development
```bash
# Container development
docker build -t omni-llm:dev .
docker run -p 8000:8080 omni-llm:dev

# Local testing
python src/lambda_function.py
curl -X POST http://localhost:8000/invoke -H "Content-Type: application/json" -d '{"prompt": "test"}'
```

### Container Testing
```bash
# Build and test container locally
docker build -t omni-llm:test .
docker run --rm omni-llm:test python -m pytest tests/

# Integration testing with ECR
pytest tests/container/ -v --docker
```

### Deployment Testing
```bash
# Deploy to staging
./deployment/scripts/deploy.sh staging

# Run integration tests against staging
pytest tests/integration/ -v --staging

# Performance testing
locust -f tests/load/locustfile.py --host=https://staging-api-url
```

## Enterprise Quality Standards

### Code Quality
- All code must pass pylint with score > 9.0
- 100% type annotation coverage with mypy
- Comprehensive error handling with structured logging
- Performance profiling for critical paths

### Documentation
- API documentation with OpenAPI 3.0 specification
- Architecture decision records (ADRs) for major changes
- Deployment runbooks for operational procedures
- Security documentation for compliance audits

### Monitoring & Observability
- CloudWatch custom metrics for business KPIs
- X-Ray tracing for end-to-end request flows
- Cost tracking and optimization recommendations
- Performance benchmarks across provider networks

## Container Optimization Guidelines

### Image Size Optimization
- Use multi-stage builds to minimize final image size
- Remove unnecessary packages and cache files
- Leverage Docker layer caching for faster builds
- Compress application assets where possible

### Runtime Performance
- Optimize Python import paths and module loading
- Use connection pooling for external API calls
- Implement intelligent caching at multiple layers
- Monitor cold start times and optimize accordingly

### Security Hardening
- Run containers with non-root user when possible
- Scan for vulnerabilities using ECR scanning
- Keep base images updated with security patches
- Follow AWS container security best practices

## Troubleshooting Guide

### Common ECR Issues
- **Authentication**: Ensure AWS CLI is configured with correct profile
- **Repository Access**: Verify IAM permissions for ECR operations
- **Image Size**: Monitor for container size limits (10GB for Lambda)
- **Vulnerability Scans**: Address security findings from ECR scanning

### Container Deployment Issues
- **Cold Starts**: Monitor and optimize container initialization
- **Memory Limits**: Adjust Lambda memory allocation based on usage
- **Network**: Verify VPC configuration for external API access
- **Logs**: Use CloudWatch for comprehensive error analysis

Remember: This is an enterprise-grade solution requiring attention to security, performance, scalability, and operational excellence at every level.