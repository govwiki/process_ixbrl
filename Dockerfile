# syntax=docker/dockerfile:1

# Use Python 3.10.4 base image
FROM python:3.10.4-alpine3.16

# Install `build-base` which is needed to build `pip` packages
RUN apk add --no-cache build-base

# Set Flask environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set the working directory
WORKDIR /app

# Install the requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy project files to `app/`
COPY . .

# Expose port 5000 (internal port)
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run"]
