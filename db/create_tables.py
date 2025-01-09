import json
import os
import boto3
import pymysql

# RDS settings
proxy_host_name = os.environ['PROXY_HOST_NAME']
port = int(os.environ['PORT'])
db_name = os.environ['DB_NAME']
db_user_name = os.environ['DB_USER_NAME']
aws_region = os.environ['AWS_REGION']
password = os.environ['PASSWORD'].strip()

# Fetch RDS Auth Token
def get_auth_token():
    client = boto3.client('rds')
    token = client.generate_db_auth_token(
        DBHostname=proxy_host_name,
        Port=port,
        DBUsername=db_user_name,
        Region=aws_region
    )
    return token

def lambda_handler():
    # token = get_auth_token()
    # print(token)
    try:
        connection = pymysql.connect(
            host=proxy_host_name,
            user=db_user_name,
            password=password,
            db=db_name,
            port=port,
            # ssl={'ca': 'Amazon RDS', 'verify_identity': False} 
        )

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mma_events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    event_name VARCHAR(255) NOT NULL,
                    event_datetime TIMESTAMP NOT NULL,
                    logo VARCHAR(255),
                    promotion VARCHAR(100),
                    location VARCHAR(100),
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (event_name)
                )
                """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bouts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    event_id INT,
                    fighter1 VARCHAR(50) NOT NULL,
                    fighter2 VARCHAR(50) NOT NULL,
                    fighter1_url VARCHAR(255),
                    fighter2_url VARCHAR(255),
                    fighter1_result VARCHAR(10),
                    fighter2_result VARCHAR(10),
                    weight_class VARCHAR(30),
                    card VARCHAR(30),
                    bout_order INT,
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES mma_events(id)
                )
                """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (name)
                )
                """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_bouts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    decision_event_id INT,
                    name VARCHAR(100) NOT NULL,
                    bout_url VARCHAR(255),
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (decision_event_id) REFERENCES decision_events(id)
                )
                """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_main_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    decision_event_id INT,
                    decision_bout_id INT,
                    judge VARCHAR(100) NOT NULL,
                    score1 INT,
                    score2 INT,
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (decision_event_id) REFERENCES decision_events(id),
                    FOREIGN KEY (decision_bout_id) REFERENCES decision_bouts(id)
                )
                """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_media_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    decision_event_id INT,
                    decision_bout_id INT,
                    judge VARCHAR(100) NOT NULL,
                    score VARCHAR(100),
                    winner VARCHAR(100),
                    record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (decision_event_id) REFERENCES decision_events(id),
                    FOREIGN KEY (decision_bout_id) REFERENCES decision_bouts(id)
                )
                """)

            result = connection.commit()
        return result
        
    except pymysql.InternalError as e:
        return (f"Error: {str(e)}")  # Return an error message if an exception occurs 
    
lambda_handler()