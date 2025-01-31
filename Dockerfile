# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install required Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests openai pillow pytesseract sqlite3

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
