import os
import pytest
from unittest.mock import patch, MagicMock
import psycopg2.pool


def test_database_url_initialization():
    fake_url = "postgresql://user:pass@remotehost:5432/proddb"
    with patch.dict(os.environ, {"DATABASE_URL": fake_url}, clear=False),          patch("psycopg2.pool.SimpleConnectionPool") as mock_pool:
        import importlib
        import database
        importlib.reload(database)

        mock_pool.assert_called_with(1, 10, dsn=fake_url)


def test_database_individual_env_fallback():
    env_vars = {
        "DB_USER": "myuser",
        "DB_PASS": "mypass",
        "DB_HOST": "dbhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb"
    }
    with patch.dict(os.environ, env_vars, clear=True),          patch("psycopg2.pool.SimpleConnectionPool") as mock_pool:
        import importlib
        import database
        importlib.reload(database)

        mock_pool.assert_called_with(
            1, 10,
            user="myuser",
            password="mypass",
            host="dbhost",
            port="5432",
            database="mydb"
        )


def test_get_and_release_connection():
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch("psycopg2.pool.SimpleConnectionPool", return_value=mock_pool):
        import importlib
        import database
        importlib.reload(database)

        conn = database.get_db_connection()
        assert conn == mock_conn
        mock_pool.getconn.assert_called_once()

        database.release_db_connection(conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)
