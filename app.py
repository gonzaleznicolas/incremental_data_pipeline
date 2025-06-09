import psycopg2
import os
import time

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        raise Exception(f"Environment variable {name} not set.")

def main():
    try:
        db_user = get_env_variable('POSTGRES_USER')
        db_password = get_env_variable('POSTGRES_PASSWORD')
        db_host = get_env_variable('POSTGRES_HOST')
        db_name = get_env_variable('POSTGRES_DB')

        conn = None
        # Retry connection to give Postgres time to initialize
        for i in range(5): # Retry 5 times
            try:
                conn = psycopg2.connect(
                    dbname=db_name,
                    user=db_user,
                    password=db_password,
                    host=db_host
                )
                print("Successfully connected to PostgreSQL!")
                break
            except psycopg2.OperationalError as e:
                print(f"Connection attempt {i+1} failed: {e}")
                if i < 4:
                    time.sleep(5) # Wait 5 seconds before retrying
                else:
                    raise

        if not conn:
            print("Failed to connect to the database after several retries.")
            return

        cur = conn.cursor()

        # Create table if it doesn't exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS greetings (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL
        );
        """)
        conn.commit()
        print("Table 'greetings' checked/created successfully.")

        # Insert data
        greeting_message = "Hello, World! (from Python to Postgres)"
        cur.execute("INSERT INTO greetings (message) VALUES (%s)", (greeting_message,))
        conn.commit()
        print(f"Inserted message: '{greeting_message}'")

        # Query data
        cur.execute("SELECT message FROM greetings ORDER BY id DESC LIMIT 1")
        retrieved_message = cur.fetchone()
        if retrieved_message:
            print(f"Retrieved message from DB: '{retrieved_message[0]}'")
        else:
            print("No message retrieved from DB.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    main()
