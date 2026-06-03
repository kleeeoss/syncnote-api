# 1. Use an official, lightweight Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
# We install libpq-dev because psycopg2 (PostgreSQL) needs C-libraries to compile
RUN apt-get update && apt-get install -y libpq-dev gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application code into the container
COPY . .

# 5. Expose the port Flask runs on
EXPOSE 5000

# 6. The command to start the API (using gunicorn for production, not standard Flask)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]