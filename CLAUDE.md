# Claude Code Instructions for Omni-LLM

## Project Context
Omni-LLM is a universal AI Lambda gateway that provides a unified API for multiple LLM providers, RAG capabilities, and MCP integration. This is a serverless AWS Lambda function designed for maximum flexibility and enterprise use.

## Development Guidelines

### Code Style
- Use Python 3.11+ with type hints
- Follow PEP 8 style guidelines
- Use async/await for I/O operations
- Implement comprehensive error handling
- Add docstrings for all public functions

### Architecture Patterns
- Use dependency injection for providers
- Implement abstract base classes for extensibility
- Use Pydantic models for data validation
- Follow the repository pattern for data access
- Implement proper separation of concerns

### Testing Requirements
- Maintain >90% test coverage
- Use pytest for testing framework
- Mock external API calls
- Test both success and failure scenarios
- Include integration tests for Lambda deployment

### Security Considerations
- Never log sensitive data (API keys, tokens)
- Validate all inputs using Pydantic
- Use AWS IAM roles for service authentication
- Implement proper error handling without data leakage
- Follow least privilege principle

### Performance Optimization
- Optimize for Lambda cold start times
- Use connection pooling where applicable
- Implement intelligent caching strategies
- Monitor and optimize memory usage
- Use ARM64 architecture for cost savings

### Deployment

#### Branch Strategy
- **`staging` branch**: Development and testing environment
- **`master` branch**: Production-ready stable releases

#### Environment-Specific Deployment
- **Staging**: `./deployment/scripts/deploy.sh staging` (1024MB, 100 req/s)
- **Production**: `./deployment/scripts/deploy.sh prod` (2048MB, 1000 req/s)

#### Pre-Deployment Checklist
- Test locally before deployment
- Run linting and type checking: `python -m pylint src/ && python -m mypy src/`
- Run tests: `python -m pytest tests/ -v --cov=src`
- Ensure .env file is configured for staging deployments
- Use AWS Secrets Manager for production API keys

#### Deployment Workflow
1. **Feature Development**: Work on `staging` branch
2. **Deploy to Staging**: Test with `./deployment/scripts/deploy.sh staging`
3. **Validation**: Thorough testing in staging environment
4. **Merge to Master**: Create PR from `staging` → `master`
5. **Production Deploy**: `./deployment/scripts/deploy.sh prod`

### File Organization
- Keep modules focused and cohesive
- Use the established project structure
- Add new providers in `src/providers/`
- Add new vector stores in `src/rag/vector_stores/`
- Update configuration models when adding features

## Key Components to Remember

1. **Multi-Provider Support**: Universal adapter pattern for all LLM providers
2. **RAG Integration**: Document processing, embedding, and retrieval
3. **MCP Protocol**: Dynamic tool discovery and execution
4. **Serverless Architecture**: Optimized for AWS Lambda constraints
5. **Enterprise Security**: Comprehensive security and compliance features