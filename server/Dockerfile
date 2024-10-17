# If building this Dockerfile standalone make sure it is built from the root directory.

FROM python:3.10.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy server requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code and the security module into the container
COPY ./server ./server
COPY ./security ./security

# Set the working directory to the server directory
WORKDIR /app/server

# Expose the necessary ports
EXPOSE 900 9001

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run when the container starts
CMD ["python", "OlafServer.py"]