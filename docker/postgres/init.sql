-- Roda automaticamente na primeira vez que o container sobe
-- (pasta /docker-entrypoint-initdb.d/ é executada pela imagem oficial do Postgres)

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
