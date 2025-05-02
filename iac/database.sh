#!/bin/bash
set -e

function sql() {
  echo $1
  aws rds-data execute-statement \
    --resource-arn ${CLUSTER_ARN} \
    --secret-arn "$2" \
    --database ${DB_NAME} \
    --sql "$1"
  echo "____"
  echo ""
}

###############################################################
# bedrock knowledge base SCHEMA
###############################################################

# add role to db using credentials
sql "CREATE ROLE ${DB_USER} WITH PASSWORD '${DB_PASSWORD}' LOGIN;" $ADMIN

# add pgvector extention
sql 'CREATE EXTENSION IF NOT EXISTS vector;' $ADMIN

# create vector SCHEMA
sql "CREATE SCHEMA IF NOT EXISTS ${SCHEMA};" $ADMIN
sql "GRANT ALL ON SCHEMA ${SCHEMA} to ${DB_USER};" $ADMIN

# use bedrock kb user to create table and index
sql "CREATE TABLE IF NOT EXISTS ${SCHEMA}.${TABLE} (
  ${PKEY} uuid PRIMARY KEY,
  ${VECTOR} vector(1536),
  ${TEXT} text,
  ${METADATA} json);
" $USER

sql "CREATE INDEX IF NOT EXISTS bedrock_kb_index ON
  ${SCHEMA}.${TABLE} USING hnsw (
    ${VECTOR} vector_cosine_ops
  );
" $USER

# Add the GIN index for the text field
sql "CREATE INDEX ON ${SCHEMA}.${TABLE} USING gin (to_tsvector('simple', ${TEXT}));" $USER

###############################################################
# application SCHEMA
###############################################################

# create conversations table/index
sql 'CREATE TABLE IF NOT EXISTS conversation (
  conversation_id UUID PRIMARY KEY,
	created TIMESTAMP WITH TIME ZONE NOT NULL,
	user_id VARCHAR NOT NULL,
	data JSONB NOT NULL
);
' $ADMIN

sql "CREATE INDEX IF NOT EXISTS conversation_id_index
  ON conversation (conversation_id);
" $ADMIN

echo "done"
