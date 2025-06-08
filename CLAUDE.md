# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese stock data collection application that automatically fetches daily OHLCV (Open, High, Low, Close, Volume) data from the J-Quants API and stores it in Google Cloud BigQuery. The system runs as a batch process on Google Cloud Platform, triggered after market close on business days.

**Implementation Status**: ✅ Production-ready - Core functionality is fully implemented and tested.

## Architecture

### Core Components
- **Data Source**: J-Quants API for Japanese stock market data
- **Processing**: Cloud Run for data fetching and processing
- **Storage**: BigQuery for persistent data storage
- **Scheduling**: Cloud Scheduler + Pub/Sub for automated triggers
- **Infrastructure**: Terraform for infrastructure as code
- **Security**: Secret Manager for API key management

### Key Design Principles
- Individual development project with cost and simplicity in mind
- Focus on essential functionality, avoiding enterprise-level complexity
- Idempotent data processing to handle duplicate runs safely
- Automatic execution on market business days only

## Database Schema

Main table: `daily_stock_prices`
- `date` (DATE, NOT NULL) - Trading date
- `security_code` (STRING, NOT NULL) - Stock symbol
- `open_price`, `high_price`, `low_price`, `close_price` (NUMERIC/FLOAT64) - OHLC prices
- `volume` (INTEGER) - Trading volume
- `created_at`, `updated_at` (TIMESTAMP) - Record metadata

Data deduplication is handled via BigQuery MERGE statements using date + security_code as the key.

## Development Standards

### Language and Environment
- Python 3.12+
- Google Cloud Platform
- Terraform for infrastructure management
- Git/GitHub for version control

### Environment Separation
- Development and production environments separated by GCP projects
- Terraform environments with separate directories (`terraform/environments/dev/` and `terraform/environments/prod/`)
- Environment-specific tfvars and backend configurations

### Error Handling Requirements
- Exponential backoff retry logic for API requests
- Graceful handling of network/server errors
- Comprehensive logging to Cloud Logging
- No automated alerting (manual log checking)

## Data Processing Flow

1. **Trigger**: Cloud Scheduler triggers daily after market close (16:00 JST)
2. **Validation**: Check if current day is a market business day
3. **Fetch**: Retrieve all available Japanese stock OHLCV data from J-Quants API
4. **Store**: MERGE data into BigQuery (preventing duplicates)
5. **Historical**: Manual trigger option for bulk historical data import

## Security Considerations

- API keys stored in Google Cloud Secret Manager
- Minimal IAM permissions for Cloud Run service accounts
- No sensitive information in code or version control

## Development Commands

### Python Development
- `python -m pytest` - Run unit tests
- `python -m pytest -v` - Run tests with verbose output
- `python -m black src/` - Format code with Black
- `python -m flake8 src/` - Lint code with Flake8
- `python -m mypy src/` - Type checking with MyPy
- `pip install -r requirements.txt` - Install dependencies

### Infrastructure Management  
- `cd terraform/environments/dev && terraform plan` - Plan infrastructure changes
- `cd terraform/environments/dev && terraform apply` - Apply infrastructure changes
- `./terraform/scripts/init.sh dev <project-id>` - Initialize environment
- `./terraform/scripts/deploy.sh dev <project-id> apply` - Deploy infrastructure
- `./terraform/scripts/update-container.sh <project-id> <region>` - Update Cloud Run container

### Local Development
- `python src/main.py` - Run Flask development server (port 8080)
- `docker build -t stock-data-collector .` - Build container image
- `docker run -p 8080:8080 stock-data-collector` - Run container locally
- `gcloud builds submit --config cloudbuild.yaml` - Build and push to GCR

## Code Architecture

### Current Implementation Status
The project is fully implemented and production-ready with the following components:

### Source Structure
- `src/main.py` - Flask application with Cloud Run endpoints:
  - `POST /` - Handles Pub/Sub messages for scheduled triggers
  - `GET /health` - Health check endpoint for Cloud Run
  - `POST /process` - Manual trigger endpoint for testing
- `src/services/` - External service clients:
  - `jquants_client.py` - J-Quants API integration using official SDK
  - `bigquery_client.py` - BigQuery operations with MERGE for idempotency
  - `secret_manager.py` - Secure credential management
- `src/models/` - Data models:
  - `stock_data.py` - StockPrice model with J-Quants/BigQuery conversions
- `src/utils/` - Shared utilities:
  - `logger.py` - Cloud Logging compatible JSON formatter
  - `retry.py` - Exponential backoff retry decorators
  - `date_utils.py` - Japanese business day handling with jpholiday
- `src/config/` - Configuration:
  - `settings.py` - Environment variable management with validation

### Key Implementation Details
- **Authentication**: Supports both refresh token (production) and email/password (development)
- **Data Processing**: Fetches all available stocks for specified dates with automatic retry
- **BigQuery Schema**: Properly partitioned by date and clustered by security_code
- **Error Handling**: Comprehensive retry logic for transient failures
- **Monitoring**: Structured JSON logging compatible with Cloud Logging

### Dependencies
- `jquants-api-client` - Official J-Quants API client
- `google-cloud-bigquery` - BigQuery operations
- `google-cloud-secret-manager` - Credential management
- `flask` - Web framework for Cloud Run
- `pandas` - Data manipulation
- `jpholiday` - Japanese holiday detection
- `tenacity` - Retry logic
- `python-dotenv` - Development environment support

### Data Flow
1. Cloud Scheduler triggers at 16:00 JST (configurable)
2. Pub/Sub message sent to Cloud Run service
3. Service validates business day using jpholiday
4. Fetches credentials from Secret Manager
5. Retrieves daily stock data from J-Quants API
6. Processes and validates data using pandas
7. Merges data into BigQuery (preventing duplicates)
8. Logs results to Cloud Logging

## Testing Strategy

### Unit Tests
- Date utilities (Japanese business day logic)
- Model conversions (J-Quants ↔ BigQuery)
- Retry logic and error handling

### Integration Tests (Manual)
1. Local Flask server with test endpoints
2. Cloud Run deployment with manual trigger
3. BigQuery data validation queries

### Test Commands
- `curl http://localhost:8080/health` - Health check
- `curl -X POST http://localhost:8080/process -H "Content-Type: application/json" -d '{"date": "2024-01-04"}'` - Manual trigger

## Deployment Process

1. **Development Testing**:
   - Run locally with Flask development server
   - Test with mock J-Quants responses
   - Validate BigQuery operations

2. **Cloud Deployment**:
   - Build container with Cloud Build
   - Deploy to Cloud Run with Terraform
   - Configure Cloud Scheduler for daily runs

3. **Production Checklist**:
   - ✅ Secret Manager configured with J-Quants credentials
   - ✅ BigQuery dataset and table created
   - ✅ Cloud Run service deployed
   - ✅ Cloud Scheduler configured for 16:00 JST
   - ✅ IAM permissions properly configured

## Monitoring and Operations

### Logging
- All logs in JSON format for Cloud Logging
- Log levels: INFO for normal operations, ERROR for failures
- Key metrics logged: records processed, API calls, processing time

### Common Operations
- **Manual data backfill**: Use `/process` endpoint with specific date
- **Check logs**: Cloud Console → Logging → Filter by resource.type="cloud_run_revision"
- **Monitor costs**: BigQuery storage and Cloud Run invocations

### Troubleshooting
- **No data collected**: Check if date is Japanese business day
- **API errors**: Verify J-Quants credentials in Secret Manager
- **BigQuery errors**: Check IAM permissions and table schema
- **Scheduler not triggering**: Verify Pub/Sub topic and subscription

## Future Enhancements (Not Implemented)
- Historical data bulk import functionality
- Data quality validation and monitoring
- Performance metrics dashboard
- Automated error alerting
- Additional market data (e.g., indices, ETFs)