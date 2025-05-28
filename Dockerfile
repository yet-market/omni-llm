# Omni-LLM Universal AI Lambda Gateway
FROM public.ecr.aws/lambda/python:3.11-arm64

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements file
COPY requirements.txt .

# Install system dependencies
RUN yum install -y gcc-c++ pkgconfig make openssl-devel

# Upgrade pip first
RUN pip install --upgrade pip

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set Python path
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

# Lambda function handler
CMD ["src.lambda_function.lambda_handler"]