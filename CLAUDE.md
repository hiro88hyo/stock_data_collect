# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese stock data collection application designed to automatically fetch daily OHLCV (Open, High, Low, Close, Volume) data from the J-Quants API and store it in Google Cloud BigQuery. The system runs as a batch process on Google Cloud Platform, triggered after market close on business days.

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
- Terraform workspaces for environment-specific configurations

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