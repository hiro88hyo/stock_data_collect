"""Tests for date utilities."""
import pytest
from datetime import date

from utils.date_utils import (
    is_japanese_business_day,
    get_latest_business_day,
    get_business_days_range,
    parse_date_string,
    format_date_for_api
)


class TestDateUtils:
    """Test date utility functions."""
    
    def test_is_japanese_business_day_weekday(self):
        """Test business day check for regular weekday."""
        # Monday, June 3, 2025
        assert is_japanese_business_day(date(2025, 6, 3)) is True
        
        # Friday, June 6, 2025
        assert is_japanese_business_day(date(2025, 6, 6)) is True
    
    def test_is_japanese_business_day_weekend(self):
        """Test business day check for weekend."""
        # Saturday, June 7, 2025
        assert is_japanese_business_day(date(2025, 6, 7)) is False
        
        # Sunday, June 8, 2025
        assert is_japanese_business_day(date(2025, 6, 8)) is False
    
    def test_is_japanese_business_day_year_end(self):
        """Test business day check for year-end holidays."""
        # December 31
        assert is_japanese_business_day(date(2025, 12, 31)) is False
        
        # January 1-3
        assert is_japanese_business_day(date(2025, 1, 1)) is False
        assert is_japanese_business_day(date(2025, 1, 2)) is False
        assert is_japanese_business_day(date(2025, 1, 3)) is False
    
    def test_get_latest_business_day(self):
        """Test getting latest business day."""
        # From a weekday
        monday = date(2025, 6, 2)
        assert get_latest_business_day(monday) == monday
        
        # From a Saturday
        saturday = date(2025, 6, 7)
        friday = date(2025, 6, 6)
        assert get_latest_business_day(saturday) == friday
        
        # From a Sunday
        sunday = date(2025, 6, 8)
        assert get_latest_business_day(sunday) == friday
    
    def test_get_business_days_range(self):
        """Test getting business days in range."""
        start = date(2025, 6, 2)  # Monday
        end = date(2025, 6, 8)    # Sunday
        
        business_days = get_business_days_range(start, end)
        
        # Should include Mon-Fri (5 days)
        assert len(business_days) == 5
        assert business_days[0] == date(2025, 6, 2)  # Monday
        assert business_days[-1] == date(2025, 6, 6)  # Friday
    
    def test_parse_date_string_various_formats(self):
        """Test parsing various date string formats."""
        # ISO format
        assert parse_date_string("2025-06-03") == date(2025, 6, 3)
        
        # Slash format
        assert parse_date_string("2025/06/03") == date(2025, 6, 3)
        
        # No separator
        assert parse_date_string("20250603") == date(2025, 6, 3)
        
        # European format
        assert parse_date_string("03/06/2025") == date(2025, 6, 3)
        assert parse_date_string("03-06-2025") == date(2025, 6, 3)
    
    def test_parse_date_string_invalid(self):
        """Test parsing invalid date string."""
        with pytest.raises(ValueError, match="Unable to parse date string"):
            parse_date_string("invalid-date")
    
    def test_format_date_for_api(self):
        """Test formatting date for API."""
        test_date = date(2025, 6, 3)
        assert format_date_for_api(test_date) == "2025-06-03"