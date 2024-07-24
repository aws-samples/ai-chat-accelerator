CREATE TABLE IF NOT EXISTS conversation (
  conversation_id UUID PRIMARY KEY,
	created TIMESTAMP WITH TIME ZONE NOT NULL,
	user_id VARCHAR NOT NULL,
	data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS conversation_id_index ON conversation (conversation_id);
