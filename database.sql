drop table if exists urls;
CREATE TABLE IF NOT EXISTS urls
(
  url_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name VARCHAR(50) NOT NULL,
  created_at DATE NOT NULL
);
drop table if exists url_checks;
CREATE TABLE IF NOT EXISTS url_checks
(
  check_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  url_id BIGINT NOT NULL,
  status_code INT,
  h1 TEXT,
  title TEXT,
  description TEXT,
  created_at DATE NOT NULL
);