"""BigQuery client implementation."""
import logging
from typing import List, Optional, Dict, Any
from datetime import date
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from models.stock_data import StockPrice
from utils.retry import default_retry

logger = logging.getLogger("stock_data_collector")


class BigQueryError(Exception):
    """BigQuery specific error."""
    pass


class BigQueryClient:
    """Client for BigQuery operations."""
    
    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        location: str = "asia-northeast1"
    ):
        """Initialize BigQuery client."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.location = location
        
        # Initialize BigQuery client
        self.client = bigquery.Client(project=project_id, location=location)
        
        # Full table reference
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        logger.info(f"Initialized BigQuery client for table: {self.table_ref}")
    
    @default_retry
    def ensure_dataset_exists(self) -> None:
        """Ensure dataset exists, create if not."""
        dataset_id_full = f"{self.project_id}.{self.dataset_id}"
        
        try:
            self.client.get_dataset(dataset_id_full)
            logger.info(f"Dataset {dataset_id_full} already exists")
        except Exception:
            logger.info(f"Creating dataset {dataset_id_full}")
            dataset = bigquery.Dataset(dataset_id_full)
            dataset.location = self.location
            dataset.description = "Dataset for Japanese stock market data"
            
            try:
                dataset = self.client.create_dataset(dataset, timeout=30)
                logger.info(f"Created dataset {dataset_id_full}")
            except Exception as e:
                if "Already Exists" not in str(e):
                    raise BigQueryError(f"Failed to create dataset: {str(e)}") from e
    
    @default_retry
    def ensure_table_exists(self) -> None:
        """Ensure table exists with correct schema, create if not."""
        table_ref_obj = bigquery.TableReference.from_string(self.table_ref)
        
        try:
            self.client.get_table(table_ref_obj)
            logger.info(f"Table {self.table_ref} already exists")
        except Exception:
            logger.info(f"Creating table {self.table_ref}")
            
            # Define schema
            schema = [
                bigquery.SchemaField("date", "DATE", mode="REQUIRED", description="Trading date"),
                bigquery.SchemaField("security_code", "STRING", mode="REQUIRED", description="Security code"),
                bigquery.SchemaField("security_name", "STRING", mode="NULLABLE", description="Security name"),
                bigquery.SchemaField("market_code", "STRING", mode="NULLABLE", description="Market code"),
                bigquery.SchemaField("open_price", "FLOAT64", mode="NULLABLE", description="Opening price"),
                bigquery.SchemaField("high_price", "FLOAT64", mode="NULLABLE", description="Highest price"),
                bigquery.SchemaField("low_price", "FLOAT64", mode="NULLABLE", description="Lowest price"),
                bigquery.SchemaField("close_price", "FLOAT64", mode="NULLABLE", description="Closing price"),
                bigquery.SchemaField("volume", "INTEGER", mode="NULLABLE", description="Trading volume"),
                bigquery.SchemaField("turnover_value", "FLOAT64", mode="NULLABLE", description="Turnover value"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="Record creation timestamp"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", description="Record update timestamp"),
            ]
            
            table = bigquery.Table(table_ref_obj, schema=schema)
            
            # Set partitioning
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            )
            
            # Set clustering
            table.clustering_fields = ["security_code"]
            
            # Set description and labels
            table.description = "Daily stock prices for Japanese market"
            table.labels = {"env": "production", "data_type": "stock_prices"}
            
            try:
                table = self.client.create_table(table, timeout=30)
                logger.info(f"Created table {self.table_ref}")
            except Exception as e:
                if "Already exists" not in str(e):
                    raise BigQueryError(f"Failed to create table: {str(e)}") from e
    
    @default_retry
    def insert_stock_data(self, stock_prices: List[StockPrice]) -> None:
        """Insert stock price data using streaming insert."""
        if not stock_prices:
            logger.warning("No stock prices to insert")
            return
        
        logger.info(f"Inserting {len(stock_prices)} stock prices")
        
        # Convert to BigQuery row format
        rows = [stock.to_bigquery_row() for stock in stock_prices]
        
        # Insert rows
        errors = self.client.insert_rows_json(self.table_ref, rows)
        
        if errors:
            logger.error(f"Failed to insert rows: {errors}")
            raise BigQueryError(f"Failed to insert rows: {errors}")
        
        logger.info(f"Successfully inserted {len(rows)} rows")
    
    @default_retry
    def merge_stock_data(self, stock_prices: List[StockPrice], target_date: date) -> None:
        """Merge stock price data using MERGE statement for idempotency."""
        if not stock_prices:
            logger.warning("No stock prices to merge")
            return
        
        logger.info(f"Merging {len(stock_prices)} stock prices for date {target_date}")
        
        # Convert to BigQuery row format
        rows = [stock.to_bigquery_row() for stock in stock_prices]
        
        # Create temporary table name
        temp_table = f"{self.table_ref}_temp_{target_date.strftime('%Y%m%d')}"
        
        try:
            # Create temporary table with data
            job_config = bigquery.QueryJobConfig(
                use_legacy_sql=False,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                destination=temp_table
            )
            
            # Insert data into temporary table
            self.client.insert_rows_json(temp_table, rows)
            
            # Execute MERGE statement
            merge_query = f"""
            MERGE `{self.table_ref}` AS target
            USING `{temp_table}` AS source
            ON target.date = source.date AND target.security_code = source.security_code
            WHEN MATCHED THEN
              UPDATE SET
                security_name = source.security_name,
                market_code = source.market_code,
                open_price = source.open_price,
                high_price = source.high_price,
                low_price = source.low_price,
                close_price = source.close_price,
                volume = source.volume,
                turnover_value = source.turnover_value,
                updated_at = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN
              INSERT (
                date, security_code, security_name, market_code,
                open_price, high_price, low_price, close_price,
                volume, turnover_value, created_at, updated_at
              )
              VALUES (
                source.date, source.security_code, source.security_name, source.market_code,
                source.open_price, source.high_price, source.low_price, source.close_price,
                source.volume, source.turnover_value, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
              )
            """
            
            # Run the merge query
            query_job = self.client.query(merge_query)
            query_job.result()  # Wait for completion
            
            logger.info(f"Successfully merged {len(rows)} rows for date {target_date}")
            
        except Exception as e:
            logger.error(f"Failed to merge data: {str(e)}")
            raise BigQueryError(f"Failed to merge data: {str(e)}") from e
        finally:
            # Clean up temporary table
            try:
                self.client.delete_table(temp_table, not_found_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temporary table: {str(e)}")
    
    def get_existing_dates(self, limit: int = 30) -> List[date]:
        """Get list of dates already in BigQuery."""
        query = f"""
        SELECT DISTINCT date
        FROM `{self.table_ref}`
        ORDER BY date DESC
        LIMIT {limit}
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            dates = [row.date for row in results]
            logger.info(f"Found {len(dates)} existing dates in BigQuery")
            return dates
            
        except Exception as e:
            logger.error(f"Failed to get existing dates: {str(e)}")
            raise BigQueryError(f"Failed to get existing dates: {str(e)}") from e
    
    def check_data_exists(self, target_date: date) -> bool:
        """Check if data for a specific date already exists."""
        query = f"""
        SELECT COUNT(*) as count
        FROM `{self.table_ref}`
        WHERE date = @target_date
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("target_date", "DATE", target_date)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            count = results[0].count if results else 0
            exists = count > 0
            
            if exists:
                logger.info(f"Data for {target_date} already exists ({count} records)")
            else:
                logger.info(f"No data found for {target_date}")
                
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check data existence: {str(e)}")
            raise BigQueryError(f"Failed to check data existence: {str(e)}") from e