"""Stock data models."""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import date, datetime


@dataclass
class StockPrice:
    """Daily stock price data model."""
    
    date: date
    security_code: str
    security_name: str
    market_code: str
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Optional[Decimal]
    volume: Optional[int]
    turnover_value: Optional[Decimal]
    
    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery row format."""
        return {
            "date": self.date.isoformat(),
            "security_code": self.security_code,
            "security_name": self.security_name,
            "market_code": self.market_code,
            "open_price": float(self.open_price) if self.open_price is not None else None,
            "high_price": float(self.high_price) if self.high_price is not None else None,
            "low_price": float(self.low_price) if self.low_price is not None else None,
            "close_price": float(self.close_price) if self.close_price is not None else None,
            "volume": self.volume,
            "turnover_value": float(self.turnover_value) if self.turnover_value is not None else None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def from_jquants_response(cls, data: dict, target_date: date) -> "StockPrice":
        """Create instance from J-Quants API response."""
        return cls(
            date=target_date,
            security_code=data.get("Code", ""),
            security_name=data.get("CompanyName", ""),
            market_code=data.get("MarketCode", ""),
            open_price=Decimal(str(data.get("Open"))) if data.get("Open") is not None else None,
            high_price=Decimal(str(data.get("High"))) if data.get("High") is not None else None,
            low_price=Decimal(str(data.get("Low"))) if data.get("Low") is not None else None,
            close_price=Decimal(str(data.get("Close"))) if data.get("Close") is not None else None,
            volume=data.get("Volume"),
            turnover_value=Decimal(str(data.get("TurnoverValue"))) if data.get("TurnoverValue") is not None else None
        )