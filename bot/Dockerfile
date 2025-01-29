# bot/Dockerfile

FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Set the PYTHONPATH environment variable
ENV PYTHONPATH="/app"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the database module
COPY ./db /app/db

# Copy the application code
COPY ./bot /app/bot

# Create the logs directory
RUN mkdir -p /app/logs

# Expose port 8000 for Gunicorn
EXPOSE 8001

# Command to run the application
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "bot.bot:app", "--bind", "0.0.0.0:8001", "--workers", "4"]