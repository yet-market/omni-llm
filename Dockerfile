# Omni-LLM Universal AI Lambda Gateway
# Multi-stage build for optimal container size and security

# Build stage
FROM public.ecr.aws/lambda/python:3.11-arm64 as builder

# Set build arguments
ARG TARGETPLATFORM=linux/arm64
ARG BUILDPLATFORM=linux/arm64

# Install system dependencies for building
RUN dnf update -y && \
    dnf install -y \
    gcc \
    gcc-c++ \
    make \
    cmake \
    git \
    && dnf clean all

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir \
    --prefer-binary \
    --target $VIRTUAL_ENV/lib/python3.11/site-packages \
    -r requirements.txt

# Production stage
FROM public.ecr.aws/lambda/python:3.11-arm64

# Set environment variables
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
COPY README.md ${LAMBDA_TASK_ROOT}/

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Create non-root user for security (Lambda will override but good practice)
RUN groupadd -r omni && useradd -r -g omni omni

# Set proper permissions
RUN chmod -R 755 ${LAMBDA_TASK_ROOT} && \
    chown -R omni:omni ${LAMBDA_TASK_ROOT}

# Health check for local development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src; print('OK')" || exit 1

# Lambda function handler
CMD ["src.lambda_function.lambda_handler"]

# Metadata labels
LABEL maintainer="Temkit Sid-Ali <contact@yet.lu>"
LABEL description="Omni-LLM Universal AI Lambda Gateway"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/yet-market/omni-llm"
LABEL org.opencontainers.image.description="A serverless AWS Lambda function for unified LLM interactions"
LABEL org.opencontainers.image.licenses="MIT"