import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

# Create a connection pool (min 1, max 10 connections)
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )
    if connection_pool:
        print("✅ Database connection pool created successfully")

except (Exception, psycopg2.DatabaseError) as error:
    print("❌ Error while connecting to PostgreSQL", error)

def get_db_connection():
    """Get a connection from the pool"""
    return connection_pool.getconn()

def release_db_connection(conn):
    """Return the connection to the pool"""
    connection_pool.putconn(conn)