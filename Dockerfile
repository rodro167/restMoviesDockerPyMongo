# Use a slim Python image to keep the image small
FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (separate layer — cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application source files (not tests, terraform, etc.)
COPY mongoRestMovies.py \
     restMoviesGuest.py \
     restMoviesAdmin.py \
     db_helpers.py \
     ./

EXPOSE 4000

CMD ["python", "mongoRestMovies.py"]
