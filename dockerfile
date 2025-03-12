# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir django djangorestframework requests gunicorn

# Expose the port the app runs on
EXPOSE 8000

# Start the Django server
CMD ["gunicorn", "movierecommender.wsgi:application", "--bind", "0.0.0.0:8000"]
