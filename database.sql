CREATE TABLE IF NOT EXISTS urls
(
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name VARCHAR(50) NOT NULL,
  created_at TIMESTAMP without time zone NOT NULL
);
