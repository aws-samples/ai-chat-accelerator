import os
import uuid
import logging
import json
import psycopg
import boto3

secrets_manager = boto3.client("secretsmanager")


class Database():
    """Encapsulate database access"""

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST")
        self.dbname = os.getenv("POSTGRES_DB")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.secret_arn = os.getenv("DB_SECRET_ARN")

    def connect(self):

        # if running in aws, fetch creds from secrets manager
        # otherwise use local creds
        if self.secret_arn is not None:
            logging.debug("fetching database credentials from secrets manager")
            secret = secrets_manager.get_secret_value(
                SecretId=self.secret_arn)
            creds = json.loads(secret["SecretString"])
            logging.debug("secret successfully fetched")
            self.user = creds["username"]
            self.password = creds["password"]

        return psycopg.connect(
            host=self.host,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )

    def new(self, user_id, created):
        """creates a new conversation"""

        id = str(uuid.uuid4())

        conversation = {
            "conversationId": id,
            "userId": user_id,
            "created": created,
            "questions": []
        }

        query = """
            INSERT INTO conversation (conversation_id, created, user_id, data)
            VALUES (%s, %s, %s, %s)
        """
        values = (id, created, user_id, json.dumps(conversation, default=str))
        logging.info(f"query: {query}")
        logging.info(f"values: {values}")

        with self.connect() as conn:
            conn.execute(query, values)

        return conversation

    def update(self, conversation):
        """updates a conversation object"""

        query = """
            UPDATE conversation
            SET data = %s
            WHERE conversation_id = %s
        """
        values = (json.dumps(conversation, default=str),
                  conversation["conversationId"])
        logging.info(f"query: {query}")
        logging.info(f"values: {values}")

        with self.connect() as conn:
            conn.execute(query, values)

    def get(self, conversation_id):
        """fetch a conversation by id"""

        query = """
            SELECT data
            FROM conversation
            WHERE conversation_id = %s
        """
        logging.info(f"query: {query}")
        values = (conversation_id,)
        logging.info(f"values: {values}")
        with self.connect() as conn:
            record = conn.execute(query, values).fetchone()

        return record[0] if record else None

    def list(self, top):
        """fetch a list of conversations"""

        query = """
            SELECT data FROM conversation
            ORDER BY created DESC
            LIMIT %s
        """
        logging.info(f"query: {query}")
        values = (top,)
        logging.info(f"values: {values}")
        with self.connect() as conn:
            records = conn.execute(query, values).fetchall()

        results = []
        for record in records:
            results.append(record[0])
        return results

    def list_by_user(self, user_id, top):
        """fetch a list of conversations by user"""

        query = """
            SELECT data FROM conversation
            WHERE user_id = %s
            ORDER BY created DESC
            LIMIT %s
        """
        logging.info(f"query: {query}")
        values = (user_id, top,)
        logging.info(f"values: {values}")
        with self.connect() as conn:
            records = conn.execute(query, values).fetchall()

        results = []
        for record in records:
            results.append(record[0])
        return results
