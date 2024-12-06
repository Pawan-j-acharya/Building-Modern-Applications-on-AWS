import os
import json
import boto3
import pymysql
from botocore.exceptions import ClientError
import logging 

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_db_connection():
    return pymysql.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        db=os.environ['DB_NAME'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_table_if_not_exists(cursor):
    # SQL statement to create the table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL
    )
    """
    cursor.execute(create_table_query)

# Lambda handler
def lambda_handler(event, context):
    logger.info("lambda function has invoked successfully")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
         # Ensure the table exists
        create_table_if_not_exists(cursor)

        # Sample users to add (you can get this from the event parameter or hardcode)
        users_to_add = [
            {"name": "John Doe", "email": "john.doe@example.com"},
            {"name": "Jane Smith", "email": "jane.smith@example.com"},
            {"name": "Alice Johnson", "email": "alice.johnson@example.com"},
        ]

        # Insert multiple users using executemany
        query = "INSERT INTO users (name, email) VALUES (%s, %s)"
        cursor.executemany(query, [(user['name'], user['email']) for user in users_to_add])

        # Commit changes to the database
        conn.commit()

        # Fetch all users from the database
        cursor.execute("SELECT * FROM users")
        all_users = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        conn.close()

        # Return the list of users
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Users added successfully", "users": all_users})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error adding users", "error": str(e)})
        }