"""J-Quants API client implementation using official jquants-api-client library."""
import logging
from typing import List, Optional
from datetime import date, datetime
from dateutil import tz
import jquantsapi

from utils.retry import api_retry
from models.stock_data import StockPrice

logger = logging.getLogger("stock_data_collector")


class JQuantsAPIError(Exception):
    """J-Quants API specific error."""
    pass


class JQuantsClient:
    """Client for J-Quants API using official jquants-api-client library."""
    
    def __init__(self, mail_address: Optional[str] = None, password: Optional[str] = None, refresh_token: Optional[str] = None):
        """Initialize J-Quants client with official library."""
        self.client: Optional[jquantsapi.Client] = None
        self.mail_address = mail_address
        self.password = password
        self.refresh_token = refresh_token
    
    def authenticate(self, refresh_token: Optional[str] = None) -> None:
        """Authenticate with J-Quants API using refresh token or credentials."""
        logger.info("Authenticating with J-Quants API")
        
        try:
            if refresh_token:
                self.client = jquantsapi.Client(refresh_token=refresh_token)
            elif self.refresh_token:
                self.client = jquantsapi.Client(refresh_token=self.refresh_token)
            elif self.mail_address and self.password:
                self.client = jquantsapi.Client(mail_address=self.mail_address, password=self.password)
            else:
                raise JQuantsAPIError("No authentication credentials provided")
            
            logger.info("Successfully authenticated with J-Quants API")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise JQuantsAPIError(f"Authentication failed: {str(e)}") from e
    
    def authenticate_with_credentials(self, email: str, password: str) -> str:
        """Authenticate with email/password and return refresh token."""
        logger.info("Authenticating with J-Quants API using credentials")
        
        try:
            temp_client = jquantsapi.Client(mail_address=email, password=password)
            refresh_token = temp_client.get_refresh_token()
            
            if not refresh_token:
                raise JQuantsAPIError("No refresh token received from API")
            
            logger.info("Successfully obtained refresh token")
            return refresh_token
            
        except Exception as e:
            logger.error(f"Credential authentication failed: {str(e)}")
            raise JQuantsAPIError(f"Credential authentication failed: {str(e)}") from e
    
    @api_retry
    def fetch_daily_quotes(self, target_date: date, code: Optional[str] = None) -> List[StockPrice]:
        """Fetch daily stock quotes for a specific date."""
        if not self.client:
            raise JQuantsAPIError("Not authenticated. Call authenticate() first.")
        
        logger.info(f"Fetching daily quotes for date: {target_date}")
        
        try:
            # Convert date to datetime with Tokyo timezone for jquants-api-client
            dt_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz.gettz("Asia/Tokyo"))
            dt_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=tz.gettz("Asia/Tokyo"))
            
            # Use get_prices_daily_quotes for single date or get_price_range for date range
            if code:
                df = self.client.get_prices_daily_quotes(code=code, date=target_date.strftime("%Y-%m-%d"))
            else:
                df = self.client.get_price_range(start_dt=dt_start, end_dt=dt_end)
            
            if df is None or df.empty:
                logger.warning(f"No data available for date: {target_date}")
                return []
            
            logger.info(f"Received {len(df)} quotes for {target_date}")
            
            # Convert DataFrame to StockPrice objects
            stock_prices = []
            for _, row in df.iterrows():
                try:
                    stock_price = StockPrice.from_dataframe_row(row, target_date)
                    stock_prices.append(stock_price)
                except Exception as e:
                    logger.warning(f"Failed to parse quote for {row.get('Code', 'Unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(stock_prices)} stock prices")
            return stock_prices
            
        except Exception as e:
            logger.error(f"Failed to fetch daily quotes: {str(e)}")
            raise JQuantsAPIError(f"Failed to fetch daily quotes: {str(e)}") from e
    
    def close(self):
        """Close the client."""
        if self.client:
            # The official jquants-api-client doesn't require explicit closing
            self.client = None