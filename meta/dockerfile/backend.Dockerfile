FROM python:3.13-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY proxy/ /app/proxy
COPY .env /app

RUN pip install --no-cache-dir -r proxy/requirements.txt

ENV PYTHONPATH=/app
# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
ENTRYPOINT ["uvicorn", "proxy.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "64"]