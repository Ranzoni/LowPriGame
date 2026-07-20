# LowPriGame

Projeto para monitorar jogos e identificar promoções em diferentes provedores.

## Como o projeto funciona

O ponto de entrada e o arquivo `main.py`.

Fluxo principal:
1. Carrega variáveis de ambiente via `.env`.
2. Configura logging no console.
3. Lê a lista de jogos em `games.json`.
4. Sincroniza os jogos no banco (adiciona novos e remove os que saíram da lista).
5. Executa uma ação:
   - `search-sales`: busca promoções e envia e-mail quando encontra.
   - `update-prices-history`: registra histórico de preços no banco.

### Fontes de dados (provedores)

Busca de promoções (`search-sales`) usa:
- IsThereAnyDeal (API)
- PSPrices (scraping)
- Buscapé (scraping)
- Kabum (scraping)
- Mercado Livre (scraping)

Registro de histórico (`update-prices-history`) usa apenas provedores de scraping:
- Buscapé
- Kabum
- Mercado Livre

### Como a comparação funciona

- O projeto calcula similaridade entre título buscado e título encontrado com `sentence-transformers`.
- Ignora termos configurados em `TERMS_TO_IGNORE`.
- Ignora links em blacklist no banco.
- Para detectar promoção no scraping, compara preço atual com a mediana dos últimos 90 dias no histórico.

## Estrutura do projeto

- `main.py`: orquestração das ações
- `games.json`: lista de jogos monitorados
- `infra/`: acesso a banco, e-mail e variáveis de ambiente
- `providers/`: integrações com APIs e scrapers
- `services/`: serviços de jogos e e-mail
- `shared/`: modelos, enums e funções utilitárias

## Requisitos

- Python 3.12+ (recomendado)
- PostgreSQL acessível pela aplicação

Dependências Python (arquivo `requirements.txt`):
- beautifulsoup4
- playwright
- psycopg[binary]
- pydantic
- python-dotenv
- requests
- sentence-transformers

## Configuração do ambiente

Na raiz do projeto:

```bash
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m playwright install chromium
```

## Variáveis de ambiente (.env)

Crie um arquivo `.env` na raiz com as chaves abaixo:

```env
# Banco
CONNECTION_STRING=postgresql://user:pass@host:5432/dbname

# E-mail
EMAIL_HOST=smtp.exemplo.com
EMAIL_USER=seu_email@exemplo.com
EMAIL_PASS=sua_senha_ou_token
EMAIL_PORT=465
EMAIL_MAX_NETWORK_RETRIES=3
EMAIL_DESTINATION=destino@exemplo.com

# Filtros de matching
TERMS_TO_IGNORE=gift card,acessorio,skin
GAME_SIMILARITY=0.88

# Provedores
BUSCAPE_URL=https://www.buscape.com.br
KABUM_URL=https://www.kabum.com.br
MERCADOLIVRE_URL=https://lista.mercadolivre.com.br
PSDPRICES_URL=https://psprices.com
ISTHERANYDEAL_API_URL=https://api.isthereanydeal.com
ISTHERANYDEAL_API_KEY=sua_api_key
ISTHERANYDEAL_API_TIMEOUT=30
```

## Estrutura mínima esperada no banco

Tabelas usadas pela aplicação:
- `games` (id, name)
- `platforms` (id, name, type)
- `game_price_history` (id, games_id, platforms_id, price, updated_at)
- `blacklist` (url)

Observação sobre `platforms.type`:
- `1` = PS5
- `2` = SWITCH

Script SQL completo de setup:
- `docs/SETUP_DB.md`

## Como executar

Use o Python do venv:

### 1) Buscar promoções

```bash
./venv/bin/python main.py search-sales
```

O que acontece:
- Consulta todos os provedores de busca.
- Registra logs detalhados no console por etapa/provedor/plataforma/jogo.
- Se encontrar promoções, monta e envia e-mail.

### 2) Registrar histórico de preços

```bash
./venv/bin/python main.py update-prices-history
```

O que acontece:
- Itera provedores de scraping.
- Busca produtos por jogo e plataforma.
- Filtra resultados válidos e persiste no histórico.

## Logs e troubleshooting

- O logging já está configurado para `INFO` no console.
- Se faltar variável de ambiente, a aplicação levanta erro informando quais chaves faltam.
- Se um provedor falhar, o erro é logado com contexto e o fluxo segue para os demais provedores.
- Se não houver promoções em `search-sales`, a aplicação finaliza sem envio de e-mail.
