# Use the official Python image
FROM python:3.11-slim

# # Set build-time variables for UID and GID
# ARG UID=1000
# ARG GID=1000

# # Create a non-root user and group with the specified UID and GID
# RUN groupadd -g $GID appuser && \
#     useradd -m -u $UID -g appuser appuser

# Set the working directory
WORKDIR /app

COPY ./db /app/db

# Copy the requirements file and install dependencies
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./flask_app /app

# Create the logs directory and set permissions
RUN mkdir -p /app/logs

# # Change ownership to the appuser
# RUN chown -R appuser:appuser /app

# # Switch to the non-root user
# USER appuser

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]