# Setup do Banco de Dados

Este arquivo descreve um script SQL base para o PostgreSQL usado pelo projeto.

Objetivo do modelo:
- Manter cadastro de jogos e plataformas.
- Registrar historico de preco por jogo e plataforma.
- Permitir blacklist de links.
- Permitir termos proibidos por jogo para ignorar resultados de scraping/API.
- Remover historico automaticamente quando um jogo ou plataforma for excluido (`ON DELETE CASCADE`).

## Script SQL

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS games (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS platforms (
    id SMALLSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type SMALLINT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS blacklist (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS terms_to_ignore (
    id BIGSERIAL PRIMARY KEY,
    games_id BIGINT NOT NULL,
    terms TEXT NOT NULL,

    CONSTRAINT fk_terms_to_ignore_game
        FOREIGN KEY (games_id)
        REFERENCES games (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_terms_to_ignore_games_id
    ON terms_to_ignore (games_id);

CREATE TABLE IF NOT EXISTS game_price_history (
    id BIGSERIAL PRIMARY KEY,
    games_id BIGINT NOT NULL,
    platforms_id SMALLINT NOT NULL,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_game_price_history_game
        FOREIGN KEY (games_id)
        REFERENCES games (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_game_price_history_platform
        FOREIGN KEY (platforms_id)
        REFERENCES platforms (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_price_history_game_platform
    ON game_price_history (games_id, platforms_id);

CREATE INDEX IF NOT EXISTS idx_game_price_history_updated_at
    ON game_price_history (updated_at DESC);

-- Valores esperados pelo enum do projeto:
-- 1 = PS5
-- 2 = SWITCH
INSERT INTO platforms (name, type)
VALUES
    ('PS5', 1),
    ('Switch', 2)
ON CONFLICT (type) DO NOTHING;

COMMIT;
```

## Observacoes

- O projeto usa as colunas `games_id` e `platforms_id` em `game_price_history`.
- Em `terms_to_ignore`, os termos podem ser armazenados separados por virgula no campo `terms`.
- Ao excluir um registro em `games` ou `platforms`, os registros relacionados em `game_price_history` serao removidos automaticamente por cascade.
- Se voce quiser apagar toda a base em ambiente de teste, use `TRUNCATE ... CASCADE` com cuidado.
