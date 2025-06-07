"""Date utilities for Japanese market business days."""
from datetime import date, datetime, timedelta
from typing import Optional, List
import jpholiday


def is_japanese_business_day(target_date: date) -> bool:
    """Check if a date is a Japanese business day."""
    # Check if weekend
    if target_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if Japanese holiday
    if jpholiday.is_holiday(target_date):
        return False
    
    # Check for specific market holidays (Year-end and New Year)
    if target_date.month == 12 and target_date.day in [31]:
        return False
    if target_date.month == 1 and target_date.day in [1, 2, 3]:
        return False
    
    return True


def get_latest_business_day(reference_date: Optional[date] = None) -> date:
    """Get the most recent business day."""
    if reference_date is None:
        reference_date = date.today()
    
    current_date = reference_date
    while not is_japanese_business_day(current_date):
        current_date = current_date - timedelta(days=1)
    
    return current_date


def get_business_days_range(start_date: date, end_date: date) -> List[date]:
    """Get list of business days in date range."""
    business_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_japanese_business_day(current_date):
            business_days.append(current_date)
        current_date = current_date + timedelta(days=1)
    
    return business_days


def parse_date_string(date_string: str) -> date:
    """Parse date string in various formats."""
    # Try different date formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
        "%d/%m/%Y",
        "%d-%m-%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date string: {date_string}")


def format_date_for_api(target_date: date) -> str:
    """Format date for J-Quants API (YYYY-MM-DD)."""
    return target_date.strftime("%Y-%m-%d")