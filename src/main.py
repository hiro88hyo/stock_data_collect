"""Main application entry point for stock data collection."""
import os
import json
import base64
from datetime import date, datetime
from typing import Dict, Any
from flask import Flask, request, jsonify
from config.settings import settings
from services.jquants_client import JQuantsClient, JQuantsAPIError
from services.bigquery_client import BigQueryClient, BigQueryError
from services.secret_manager import SecretManagerClient, SecretManagerError
from utils.logger import setup_logging
from utils.date_utils import (
    is_japanese_business_day,
    get_latest_business_day,
    parse_date_string
)
import jquantsapi

# Set up logging
logger = setup_logging(settings.log_level)

# Initialize Flask app
app = Flask(__name__)


def decode_pubsub_message(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Decode Pub/Sub message from request."""
    if not envelope:
        raise ValueError("No Pub/Sub message received")

    pubsub_message = envelope.get("message", {})

    if isinstance(pubsub_message, dict) and "data" in pubsub_message:
        data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        return json.loads(data)

    return {}


def process_stock_data(target_date: date, force: bool = False) -> Dict[str, Any]:
    """Process stock data for a specific date."""
    logger.info(f"Processing stock data for date: {target_date}")

    # Initialize clients
    try:
        # Initialize service clients
        secret_client = SecretManagerClient(settings.project_id)
        jquants_client = JQuantsClient(settings.jquants_base_url, settings.timeout_seconds)
        bigquery_client = BigQueryClient(
            settings.project_id,
            settings.bigquery_dataset,
            settings.bigquery_table,
            settings.bigquery_location
        )

        # Ensure BigQuery resources exist
        bigquery_client.ensure_dataset_exists()
        bigquery_client.ensure_table_exists()

    except Exception as e:
        logger.error(f"Failed to initialize clients: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to initialize clients: {str(e)}",
            "date": target_date.isoformat()
        }

    # Check if it's a business day (unless forced)
    if not force and not is_japanese_business_day(target_date):
        logger.info(f"{target_date} is not a Japanese business day, skipping")
        return {
            "status": "skipped",
            "message": f"{target_date} is not a business day",
            "date": target_date.isoformat()
        }

    # Check if data already exists (unless forced)
    if not force:
        try:
            if bigquery_client.check_data_exists(target_date):
                logger.info(f"Data for {target_date} already exists, skipping")
                return {
                    "status": "skipped",
                    "message": f"Data for {target_date} already exists",
                    "date": target_date.isoformat()
                }
        except Exception as e:
            logger.warning(f"Failed to check existing data: {str(e)}")

    # Get J-Quants API credentials
    try:
        # Try to get refresh token from Secret Manager
        refresh_token = None
        if settings.environment == "production":
            refresh_token = secret_client.get_refresh_token(settings.jquants_refresh_token_secret)
        else:
            # In development, check environment variables first
            if settings.jquants_email and settings.jquants_password:
                logger.info("Using email/password authentication for development")
                refresh_token = jquants_client.authenticate_with_credentials(
                    settings.jquants_email,
                    settings.jquants_password
                )
            else:
                # Try Secret Manager as fallback
                try:
                    refresh_token = secret_client.get_refresh_token(settings.jquants_refresh_token_secret)
                except SecretManagerError:
                    logger.warning("No refresh token found, trying credentials from Secret Manager")
                    email, password = secret_client.get_jquants_credentials()
                    if email and password:
                        refresh_token = jquants_client.authenticate_with_credentials(email, password)
        
        if not refresh_token:
            raise ValueError("No J-Quants authentication credentials available")
        
        # Authenticate with J-Quants API
        jquants_client.authenticate(refresh_token)
        
    except Exception as e:
        logger.error(f"Failed to authenticate with J-Quants API: {str(e)}")
        return {
            "status": "error",
            "message": f"Authentication failed: {str(e)}",
            "date": target_date.isoformat()
        }
    
    # Fetch stock data
    try:
        stock_prices = jquants_client.fetch_daily_quotes(target_date)
        
        if not stock_prices:
            logger.warning(f"No stock data available for {target_date}")
            return {
                "status": "no_data",
                "message": f"No stock data available for {target_date}",
                "date": target_date.isoformat(),
                "count": 0
            }
        
        logger.info(f"Fetched {len(stock_prices)} stock prices for {target_date}")
        
    except JQuantsAPIError as e:
        logger.error(f"Failed to fetch stock data: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch data: {str(e)}",
            "date": target_date.isoformat()
        }
    finally:
        jquants_client.close()
    
    # Store data in BigQuery
    try:
        # Use MERGE for idempotent inserts
        bigquery_client.merge_stock_data(stock_prices, target_date)
        
        logger.info(f"Successfully stored {len(stock_prices)} stock prices for {target_date}")
        
        return {
            "status": "success",
            "message": f"Successfully processed {len(stock_prices)} stock prices",
            "date": target_date.isoformat(),
            "count": len(stock_prices)
        }
        
    except BigQueryError as e:
        logger.error(f"Failed to store data in BigQuery: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to store data: {str(e)}",
            "date": target_date.isoformat()
        }


@app.route("/", methods=["POST"])
def handle_pubsub_message():
    """Handle Pub/Sub message for stock data collection."""
    try:
        # Parse Pub/Sub message
        envelope = request.get_json()
        if not envelope:
            logger.error("No Pub/Sub message received")
            return jsonify({"error": "No Pub/Sub message received"}), 400
        
        # Decode message
        message_data = decode_pubsub_message(envelope)
        
        # Extract parameters
        trigger_type = message_data.get("trigger_type", "daily")
        date_str = message_data.get("date")
        force = message_data.get("force", False)
        
        # Determine target date
        if date_str:
            target_date = parse_date_string(date_str)
        else:
            # Use latest business day
            target_date = get_latest_business_day()
        
        logger.info(f"Received {trigger_type} trigger for date: {target_date}")
        
        # Process stock data
        result = process_stock_data(target_date, force=force)
        
        # Log processing result
        logger.info(f"Processing result: {result}")
        
        # Acknowledge message
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }), 200


@app.route("/process", methods=["POST"])
def manual_process():
    """Manual trigger endpoint for testing."""
    try:
        # Get request data
        data = request.get_json() or {}
        
        # Extract parameters
        date_str = data.get("date")
        force = data.get("force", False)
        
        # Determine target date
        if date_str:
            target_date = parse_date_string(date_str)
        else:
            target_date = get_latest_business_day()
        
        # Process stock data
        result = process_stock_data(target_date, force=force)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid request: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Manual process error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Processing failed: {str(e)}"
        }), 500


if __name__ == "__main__":
    # Run Flask app
    port = int(os.environ.get("PORT", settings.port))
    debug = settings.debug
    
    logger.info(f"Starting stock data collector on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)