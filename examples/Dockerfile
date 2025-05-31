FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Install system dependencies
RUN yum install -y gcc-c++ pkgconfig make

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p /var/task/shared

# Copy shared utilities
COPY shared/ /var/task/shared/

# Copy function code
COPY lambda_function.py .

# Set Python path
ENV PYTHONPATH=/var/task

# Set command for container
CMD ["lambda_function.lambda_handler"]