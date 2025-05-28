#!/bin/bash

# Omni-LLM Development Setup Script
# =================================
# Sets up the local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

print_status "Setting up Omni-LLM development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python version check passed: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements-dev.txt

print_success "Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp ENV_TEMPLATE.env .env
    
    print_warning "Please edit .env file and add your API keys:"
    print_warning "- OPENAI_API_KEY"
    print_warning "- ANTHROPIC_API_KEY (optional)"
    print_warning "- Other provider keys as needed"
    
    # Set development API key
    echo "OMNI_LLM_API_KEYS=dev-key-12345,test-key-67890" >> .env
else
    print_status ".env file already exists"
fi

# Create necessary directories
print_status "Creating project directories..."
mkdir -p deployment/build
mkdir -p logs
mkdir -p tests/fixtures

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    print_status "Installing pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not found, skipping hook installation"
fi

# Run basic tests to verify setup
print_status "Running basic tests..."
python -c "
import sys
sys.path.append('src')
from src.models.architecture import OMNI_LLM_ARCHITECTURE
print('✓ Architecture models loaded successfully')

from src.utils.config import Config
config = Config()
print('✓ Configuration loaded successfully')

from src.core.validators import validate_request
print('✓ Validators loaded successfully')
"

if [ $? -eq 0 ]; then
    print_success "Basic tests passed"
else
    print_error "Basic tests failed"
    exit 1
fi

# Create development scripts
print_status "Creating development scripts..."

# Create start-dev script
cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
# Start local development server

source venv/bin/activate
export PYTHONPATH="$PWD/src:$PYTHONPATH"

if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Run setup-dev.sh first."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo "Starting Omni-LLM development server..."
echo "API will be available at: http://localhost:8000"
echo "Documentation at: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo
echo "Test with development API key: dev-key-12345"
echo

python src/lambda_function.py
EOF

chmod +x scripts/start-dev.sh

# Create test script
cat > scripts/test.sh << 'EOF'
#!/bin/bash
# Run tests

source venv/bin/activate
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

echo "Running tests..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo "Running type checks..."
mypy src/

echo "Running linting..."
flake8 src/
EOF

chmod +x scripts/test.sh

# Create format script
cat > scripts/format.sh << 'EOF'
#!/bin/bash
# Format code

source venv/bin/activate

echo "Formatting code with black..."
black src/ tests/

echo "Sorting imports with isort..."
isort src/ tests/

echo "Code formatting complete!"
EOF

chmod +x scripts/format.sh

print_success "Development scripts created"

# Display usage information
echo
echo "=================================================================="
echo "                 DEVELOPMENT SETUP COMPLETE"
echo "=================================================================="
echo
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Start development server: ./scripts/start-dev.sh"
echo "3. Run tests: ./scripts/test.sh"
echo "4. Format code: ./scripts/format.sh"
echo
echo "Development endpoints:"
echo "- API: http://localhost:8000/invoke"
echo "- Health: http://localhost:8000/health"
echo "- Docs: http://localhost:8000/docs"
echo
echo "Test API call:"
echo 'curl -X POST http://localhost:8000/invoke \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "x-api-key: dev-key-12345" \'
echo '  -d '"'"'{"prompt": "Hello!", "model_provider": "openai", "model_name": "gpt-3.5-turbo"}'"'"
echo
echo "=================================================================="

print_success "Development environment ready!"