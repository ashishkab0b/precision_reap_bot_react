# flask_app/Dockerfile


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
COPY ./flask_app /app/flask_app

# Create the logs directory
RUN mkdir -p /app/logs

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "flask_app.run:app"]