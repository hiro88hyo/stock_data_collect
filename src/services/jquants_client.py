"""J-Quants API client implementation."""
import logging
from typing import List, Dict, Optional, Any
from datetime import date
import requests
from requests.exceptions import HTTPError

from ..utils.retry import api_retry
from ..utils.date_utils import format_date_for_api
from ..models.stock_data import StockPrice

logger = logging.getLogger("stock_data_collector")


class JQuantsAPIError(Exception):
    """J-Quants API specific error."""
    pass


class JQuantsClient:
    """Client for J-Quants API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize J-Quants client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def authenticate(self, refresh_token: str) -> None:
        """Authenticate with J-Quants API using refresh token."""
        logger.info("Authenticating with J-Quants API")
        
        try:
            response = self._make_request(
                "POST",
                "/token/auth_refresh",
                params={"refreshtoken": refresh_token}
            )
            
            self.access_token = response.get("idToken")
            if not self.access_token:
                raise JQuantsAPIError("No access token received from API")
            
            # Update session headers with token
            self.session.headers["Authorization"] = f"Bearer {self.access_token}"
            logger.info("Successfully authenticated with J-Quants API")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise JQuantsAPIError(f"Authentication failed: {str(e)}") from e
    
    def authenticate_with_credentials(self, email: str, password: str) -> str:
        """Authenticate with email/password and return refresh token."""
        logger.info("Authenticating with J-Quants API using credentials")
        
        try:
            response = self._make_request(
                "POST",
                "/token/auth_user",
                json={"mailaddress": email, "password": password}
            )
            
            refresh_token = response.get("refreshToken")
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
        if not self.access_token:
            raise JQuantsAPIError("Not authenticated. Call authenticate() first.")
        
        date_str = format_date_for_api(target_date)
        logger.info(f"Fetching daily quotes for date: {date_str}")
        
        params = {"date": date_str}
        if code:
            params["code"] = code
        
        try:
            response = self._make_request("GET", "/prices/daily_quotes", params=params)
            
            # Response should contain 'daily_quotes' key with list of quotes
            quotes_data = response.get("daily_quotes", [])
            logger.info(f"Received {len(quotes_data)} quotes for {date_str}")
            
            # Convert to StockPrice objects
            stock_prices = []
            for quote in quotes_data:
                try:
                    stock_price = StockPrice.from_jquants_response(quote, target_date)
                    stock_prices.append(stock_price)
                except Exception as e:
                    logger.warning(f"Failed to parse quote for {quote.get('Code', 'Unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(stock_prices)} stock prices")
            return stock_prices
            
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No data available for date: {date_str}")
                return []
            raise
        except Exception as e:
            logger.error(f"Failed to fetch daily quotes: {str(e)}")
            raise JQuantsAPIError(f"Failed to fetch daily quotes: {str(e)}") from e
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to J-Quants API."""
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"Making {method} request to {url}")
        
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=self.timeout
        )
        
        # Check for HTTP errors
        try:
            response.raise_for_status()
        except HTTPError as e:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"API request failed: {error_msg}")
            raise HTTPError(error_msg) from e
        
        # Parse JSON response
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {response.text}")
            raise JQuantsAPIError(f"Invalid JSON response: {response.text}") from e
    
    def close(self):
        """Close the session."""
        self.session.close()