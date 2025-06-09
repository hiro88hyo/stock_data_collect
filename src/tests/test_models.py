"""Tests for stock data models."""
from datetime import date
from decimal import Decimal

from models.stock_data import StockPrice


class TestStockPrice:
    """Test StockPrice model."""
    
    def test_stock_price_creation(self):
        """Test creating a StockPrice instance."""
        stock = StockPrice(
            date=date(2025, 6, 3),
            security_code="7203",
            open_price=Decimal("2500.0"),
            high_price=Decimal("2520.0"),
            low_price=Decimal("2480.0"),
            close_price=Decimal("2510.0"),
            volume=1000000,
            turnover_value=Decimal("2505000000")
        )
        
        assert stock.date == date(2025, 6, 3)
        assert stock.security_code == "7203"
        assert stock.open_price == Decimal("2500.0")
        assert stock.volume == 1000000
    
    def test_to_bigquery_row(self):
        """Test converting to BigQuery row format."""
        stock = StockPrice(
            date=date(2025, 6, 3),
            security_code="7203",
            open_price=Decimal("2500.0"),
            high_price=Decimal("2520.0"),
            low_price=Decimal("2480.0"),
            close_price=Decimal("2510.0"),
            volume=1000000,
            turnover_value=Decimal("2505000000")
        )
        
        row = stock.to_bigquery_row()
        
        assert row["date"] == "2025-06-03"
        assert row["security_code"] == "7203"
        assert row["open_price"] == 2500.0
        assert row["volume"] == 1000000
        assert "created_at" in row
        assert "updated_at" in row
    
    def test_to_bigquery_row_with_nulls(self):
        """Test converting to BigQuery row with null values."""
        stock = StockPrice(
            date=date(2025, 6, 3),
            security_code="7203",
            open_price=None,
            high_price=None,
            low_price=None,
            close_price=None,
            volume=None,
            turnover_value=None
        )
        
        row = stock.to_bigquery_row()
        
        assert row["open_price"] is None
        assert row["high_price"] is None
        assert row["volume"] is None
    
    def test_from_jquants_response(self):
        """Test creating from J-Quants API response."""
        response_data = {
            "Date": "2025-06-03",
            "Code": "7203",
            "Open": 2500.0,
            "High": 2520.0,
            "Low": 2480.0,
            "Close": 2510.0,
            "Volume": 1000000,
            "TurnoverValue": 2505000000
        }
        
        target_date = date(2025, 6, 3)
        stock = StockPrice.from_jquants_response(response_data, target_date)
        
        assert stock.date == target_date
        assert stock.security_code == "7203"
        assert stock.open_price == Decimal("2500.0")
        assert stock.volume == 1000000
    
    def test_from_jquants_response_with_nulls(self):
        """Test creating from J-Quants response with null values."""
        response_data = {
            "Code": "7203",
            "Open": None,
            "High": None,
            "Low": None,
            "Close": None,
            "Volume": None,
            "TurnoverValue": None
        }
        
        target_date = date(2025, 6, 3)
        stock = StockPrice.from_jquants_response(response_data, target_date)
        
        assert stock.date == target_date
        assert stock.security_code == "7203"
        assert stock.open_price is None
        assert stock.volume is None