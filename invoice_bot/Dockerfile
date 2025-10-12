# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# No additional OCR setup needed - EasyOCR uses pure Python with torch
# EasyOCR models will be downloaded automatically on first use

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port if your Tkinter app needs to be accessed via X-server (less common for bots)
# For a headless bot, this might not be necessary.
# ENV DISPLAY=:0

# Command to run the application
# This will run the Tkinter GUI. For headless operation, you might run a CLI version of main.py
CMD ["python", "src/main.py"]
