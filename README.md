# Data Product Concierge

Enterprise Streamlit application for managing data product metadata in Collibra with AI-powered assistance and Snowflake integration.

## Description

Data Product Concierge is a comprehensive data governance and product management platform designed for enterprise asset management firms. It provides:

- **Data Product Registry**: Centralized management of data products in Collibra with rich metadata
- **AI-Assisted Specification**: LLM-powered guidance for completing data product specifications
- **Multi-Cloud Integration**: Seamless connectivity with Collibra, Snowflake, OpenAI/Bedrock, and AWS
- **Enterprise Security**: OAuth2 authentication via APIM Gateway, encrypted credentials, role-based access
- **Metadata Governance**: Complete capture of business context, regulatory requirements, and data quality metrics
- **Audit Trail**: Full tracking of specifications through PostgreSQL backend

## Architecture Overview

The application follows a layered architecture:

```
┌─────────────────────────────────────────────────────┐
│           Streamlit UI Layer                        │
│  (Data product form, visualization, download)       │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│         Business Logic Layer                        │
│  (DataProductSpec, validation, transformations)     │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│         Integration Clients                         │
│  (Collibra, Snowflake, OpenAI/Bedrock, PostgreSQL) │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│         External Services & Data Stores             │
│  (APIM Gateway, APIs, Cloud Services, Database)     │
└─────────────────────────────────────────────────────┘
```

### Key Components

- **DataProductSpec**: Pydantic model representing complete data product specification (90+ fields)
- **CollibraClient**: REST API wrapper with OAuth2 authentication, asset CRUD, metadata management
- **PostgreSQL**: Audit trail, draft storage, version history
- **LLM Integration**: AI-powered field completion and requirement analysis

## Quick Start

1. **Clone and setup**
   ```bash
   git clone <repo>
   cd data-product-concierge
   cp .env.example .env
   ```

2. **Configure environment**
   ```bash
   # Edit .env with your firm's APIM and Collibra details
   vi .env
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access application**
   ```bash
   open http://localhost:8501
   ```

5. **Run tests**
   ```bash
   docker-compose exec app pytest -v
   ```

## Configuration Reference

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `APIM_BASE_URL` | APIM Gateway endpoint | Yes | `https://api-gateway.firm.com` |
| `APIM_CLIENT_ID` | OAuth2 client ID | Yes | `dpc-app` |
| `APIM_CLIENT_SECRET` | OAuth2 client secret | Yes | `sk-...` |
| `APIM_SUBSCRIPTION_KEY` | API subscription key | Yes | `abc123xyz` |
| `COLLIBRA_INSTANCE_URL` | Collibra instance URL | Yes | `https://firm.collibra.com` |
| `DATA_PRODUCT_TYPE_ID` | Collibra resource type UUID | Yes | `00000000-0000-...` |
| `COLLIBRA_ATTR_*` | Attribute type UUIDs (27 total) | Yes | `00000000-0000-...` |
| `COLLIBRA_VOCAB_*` | Vocabulary domain UUIDs (9 total) | Yes | `00000000-0000-...` |
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://user:pass@host/db` |
| `LLM_PROVIDER` | LLM backend (openai/bedrock) | Yes | `openai` |
| `OPENAI_API_KEY` | OpenAI API key (if openai) | Conditional | `sk-...` |
| `OPENAI_MODEL` | OpenAI model name | Conditional | `gpt-4o` |
| `AWS_REGION` | AWS region (if bedrock) | Conditional | `eu-west-1` |
| `BEDROCK_MODEL_ID` | Bedrock model ID (if bedrock) | Conditional | `anthropic.claude-3-...` |
| `FIRM_NAME` | Firm branding | Yes | `Your Asset Management Firm` |

All 50+ environment variables are documented in `.env.example`.

## Development Setup

### Local Installation

```bash
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run app.py
```

### Database Migrations

```bash
alembic upgrade head
```

## Testing

### Run All Tests

```bash
pytest -v --cov=. --cov-report=html
```

### Run Specific Test Suite

```bash
# Unit tests for data models
pytest tests/test_data_product_model.py -v

# Integration tests (requires live API)
pytest tests/test_collibra_client.py -v

# Coverage report
pytest --cov=. --cov-report=term-missing
```

### Test Categories

**Unit Tests** (`tests/test_data_product_model.py`):
- Model creation and validation
- Field completion percentage calculation
- Markdown and JSON serialization
- CSV export formatting
- Email and numeric validation

**Integration Tests** (`tests/test_collibra_client.py`):
- Asset search and retrieval
- Metadata attribute operations
- Vocabulary lookup
- Create/update roundtrips
- Real API calls (skipped if APIM unavailable)

## Deployment

### Docker Deployment

```bash
docker-compose up -d
docker-compose logs -f app
docker-compose down
```

### Environment-Specific Configurations

Create environment-specific .env files:
- `.env.dev` - Development settings
- `.env.staging` - Staging settings
- `.env.prod` - Production settings

Override with: `docker-compose --env-file .env.prod up -d`

### Health Checks

The application includes Docker health checks:
- Streamlit health endpoint: `http://localhost:8501/_stcore/health`
- PostgreSQL: `pg_isready` command
- APIM connectivity: Tested on startup

## Project Structure

```
data-product-concierge/
├── app.py                      # Streamlit application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Multi-service orchestration
├── .env.example               # Environment template
├── README.md                  # This file
├── models/
│   └── data_product.py        # DataProductSpec Pydantic model
├── clients/
│   ├── collibra.py           # Collibra REST client
│   ├── snowflake.py          # Snowflake connector
│   ├── llm.py                # OpenAI/Bedrock wrapper
│   └── database.py           # PostgreSQL async client
├── services/
│   ├── auth.py               # APIM OAuth2 auth
│   ├── transformers.py       # Format conversion logic
│   └── validators.py         # Data validation rules
├── ui/
│   ├── forms.py              # Streamlit form components
│   └── pages/                # Multi-page app sections
├── tests/
│   ├── __init__.py
│   ├── test_data_product_model.py
│   ├── test_collibra_client.py
│   ├── conftest.py           # Pytest fixtures
│   └── fixtures/             # Test data
└── migrations/               # Alembic database migrations
```

## License

Proprietary - All rights reserved to [Your Firm]

## Support

For issues or questions:
1. Check the `.env.example` for configuration
2. Review test files for usage examples
3. Enable debug logging: `export STREAMLIT_LOGGER_LEVEL=debug`
4. Contact the Data Governance team
