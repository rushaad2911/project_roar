FROM python:3.11-slim

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/

# Install python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

CMD ["gunicorn", "project_roar.wsgi:application", "--bind", "0.0.0.0:8000"]
