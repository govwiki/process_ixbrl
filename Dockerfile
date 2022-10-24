# syntax=docker/dockerfile:1

# Use Python 3.10.4 base image
FROM python:3.10.4-alpine3.16

# Get the base domain
ARG BASE_DOMAIN

# Set the base domain
ENV BASE_DOMAIN="${BASE_DOMAIN}"

# Install `build-base` which is needed to build `pip` packages
RUN apk add --no-cache build-base

# Install the required packages for `weasyprint`
# Source: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#alpine-3-12
RUN apk add --no-cache py3-pip py3-pillow py3-cffi py3-brotli gcc musl-dev python3-dev pango

# Install `fontconfig` (required by `weasyprint`)
RUN apk --no-cache add fontconfig ttf-freefont font-noto terminus-font

# Set the working directory
WORKDIR /app

# Install `git` as it is needed by `pip` to install
# the requirements (for drkane's `ixbrlparse` fork).
RUN apk add --no-cache git

# Install the requirements
COPY requirements.txt requirements.txt
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip pip install -r requirements.txt

# Copy project files to `app/`
COPY . .

# Expose port 5000 (internal port)
EXPOSE 5000

# Set Flask environment variables
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Create `upload/`
RUN mkdir -p upload

# Run the Flask app
CMD ["flask", "run"]
