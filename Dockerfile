# Use an official Python runtime as a parent image
# Using a "slim" version keeps the final container smaller
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the file that lists the dependencies
COPY r./AutoBot/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./utils ./utils
# Copy the rest of your application's code into the container
COPY ./AutoBot .

# Command to run your bot when the container launches
CMD ["python", "-u", "main.py"]