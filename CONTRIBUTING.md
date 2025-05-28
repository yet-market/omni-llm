# Contributing to Omni-LLM

We love your input! We want to make contributing to Omni-LLM as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### 1. Fork the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/omni-llm.git
   cd omni-llm
   ```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy environment template
cp ENV_TEMPLATE.env .env
# Edit .env with your API keys for testing
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 4. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 5. Test Your Changes

```bash
# Run all tests
pytest tests/ -v --cov=src

# Run linting
python -m pylint src/
python -m mypy src/

# Test locally
python src/lambda_function.py
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "feat: add amazing new feature"
# Follow conventional commit format
```

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📝 Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build
2. Update the README.md with details of changes to the interface, including new environment variables, exposed ports, useful file locations, and container parameters
3. Update the CHANGELOG.md with a note describing your changes
4. Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent
5. Your pull request will be merged once you have the sign-off of at least one maintainer

## 🎯 Areas for Contribution

### 🆕 New Provider Integrations
We're always looking to add support for new LLM providers:

- **Emerging Providers**: New AI companies and their models
- **Enterprise Solutions**: Private cloud and on-premise solutions
- **Specialized Models**: Domain-specific or fine-tuned models

**Template for new providers:**
```python
# src/providers/new_provider.py
from .base_provider import BaseProvider

class NewProvider(BaseProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        # Implementation here
```

### 🔧 Feature Enhancements
- **Performance Optimizations**: Improve speed and reduce costs
- **New Structured Output Formats**: Additional schema types
- **Enhanced RAG Capabilities**: Better document processing
- **Advanced MCP Features**: Extended tool support

### 📚 Documentation
- **API Examples**: Real-world usage scenarios
- **Deployment Guides**: Different cloud platforms
- **Performance Tuning**: Optimization best practices
- **Troubleshooting**: Common issues and solutions

### 🐛 Bug Fixes
- **Provider Issues**: API integration problems
- **Performance Bugs**: Memory leaks, slow responses
- **Edge Cases**: Unusual input handling
- **Security Issues**: Vulnerability fixes

## 🎨 Code Style Guidelines

### Python Code Style
We follow PEP 8 with some modifications:

- **Line Length**: 120 characters maximum
- **Imports**: Use absolute imports, group by standard library, third-party, local
- **Type Hints**: All functions should have type hints
- **Docstrings**: Use Google-style docstrings

```python
def process_request(
    prompt: str,
    model_provider: str,
    model_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process an LLM request with the specified provider.
    
    Args:
        prompt: The input prompt for the model
        model_provider: The LLM provider to use
        model_config: Optional configuration parameters
        
    Returns:
        Dictionary containing the response and metadata
        
    Raises:
        ValueError: If provider is not supported
        ConnectionError: If provider API is unavailable
    """
    # Implementation here
```

### Commit Message Format
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect meaning (white-space, formatting)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(providers): add support for Cohere Command R+ model
fix(rag): resolve vector store connection timeout issue
docs(api): update structured output examples
perf(lambda): optimize cold start time by 40%
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_providers/     # Provider-specific tests
│   ├── test_rag/          # RAG functionality tests
│   └── test_mcp/          # MCP integration tests
├── integration/            # Integration tests
│   ├── test_full_workflow.py
│   └── test_real_providers.py
└── load/                   # Load testing
    └── locustfile.py
```

### Writing Tests
```python
import pytest
from unittest.mock import patch, MagicMock
from src.providers.openai_provider import OpenAIProvider

class TestOpenAIProvider:
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = OpenAIProvider(api_key="test-key")
    
    @patch('openai.ChatCompletion.create')
    def test_basic_chat_completion(self, mock_create):
        """Test basic chat completion functionality."""
        # Arrange
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        
        # Act
        result = self.provider.chat_completion("Hello")
        
        # Assert
        assert result["content"] == "Test response"
        mock_create.assert_called_once()
```

### Test Coverage
- Maintain >90% test coverage
- Test both success and failure scenarios
- Include edge cases and error conditions
- Mock external API calls

## 🔒 Security Guidelines

### API Key Handling
- Never commit API keys or secrets
- Use environment variables or AWS Secrets Manager
- Validate and sanitize all inputs
- Log responses without sensitive data

### Code Security
- Validate all user inputs
- Use parameterized queries for databases
- Implement proper error handling without data leakage
- Follow AWS security best practices

## 📋 Issue Templates

### Bug Report
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Send request with parameters: '...'
2. Observe response: '...'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.11]
- AWS Lambda runtime: [e.g., python3.11]
- Provider: [e.g., OpenAI, Anthropic]

**Additional context**
Add any other context about the problem here.
```

### Feature Request
```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions.

**Provider/Technology**
If applicable, which LLM provider or technology this relates to.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 🏆 Recognition

Contributors will be recognized in the following ways:

- **Contributors Section**: Added to README.md
- **Release Notes**: Mentioned in CHANGELOG.md
- **GitHub Contributors**: Automatic GitHub recognition
- **Special Thanks**: Major contributors highlighted

## 📞 Getting Help

- **GitHub Discussions**: For questions and general discussions
- **GitHub Issues**: For bugs and feature requests
- **Email**: [contact@yet.lu](mailto:contact@yet.lu) for sensitive issues

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You

Thank you for contributing to Omni-LLM! Your efforts help make AI more accessible to developers worldwide. Every contribution, no matter how small, makes a difference.

**Happy coding! 🚀**