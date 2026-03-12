from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)

from src.database.base import Base


class DimCurrency(Base):
    __tablename__ = "dim_currency"
    __table_args__ = (
        UniqueConstraint("base_currency", "quote_currency"),
        UniqueConstraint("currency_pair_code"),
        UniqueConstraint("currency_pair_symbol"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_currency = Column(CHAR(3), nullable=False)
    quote_currency = Column(CHAR(3), nullable=False)
    currency_pair_code = Column(Text, nullable=False)
    currency_pair_symbol = Column(Text, nullable=False)


class DimTimeframe(Base):
    __tablename__ = "dim_timeframe"
    __table_args__ = (
        UniqueConstraint("timeframe_code"),
        UniqueConstraint("duration_seconds"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timeframe_code = Column(Text, nullable=False)
    timeframe_name = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=False)


class FactBuySellEvents(Base):
    __tablename__ = "fact_buysell_events"
    __table_args__ = (
        PrimaryKeyConstraint(
            "event_datetime",
            "currency_id",
            "event_type",
            "trigger_indicator_name",
        ),
    )

    event_id = Column(Integer, autoincrement=True)
    event_datetime = Column(DateTime, nullable=False)
    currency_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    event_type = Column(String(10), nullable=False)
    trigger_indicator_name = Column(String(10), nullable=False)
    trigger_indicator_value = Column(Float, nullable=False)
    trigger_indicator_timeframe = Column(String(10), nullable=False)
    trigger_indicator_period = Column(Integer, nullable=False)


class FactEma(Base):
    __tablename__ = "fact_ema"
    __table_args__ = (
        PrimaryKeyConstraint(
            "time",
            "currency_id",
            "timeframe_id",
            "period",
            "calc_version",
        ),
    )

    time = Column(DateTime, nullable=False)
    currency_id = Column(Integer, ForeignKey("dim_currency.id"), nullable=False)
    timeframe_id = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    calc_version = Column(Text, nullable=False)
    value = Column(Float)
    calculated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class FactRsi(Base):
    __tablename__ = "fact_rsi"
    __table_args__ = (
        PrimaryKeyConstraint(
            "time",
            "currency_id",
            "timeframe_id",
            "period",
            "calc_version",
        ),
    )

    time = Column(DateTime, nullable=False)
    currency_id = Column(Integer, ForeignKey("dim_currency.id"), nullable=False)
    timeframe_id = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    calc_version = Column(Text, nullable=False)
    value = Column(Float)
    calculated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class FactSma(Base):
    __tablename__ = "fact_sma"
    __table_args__ = (
        PrimaryKeyConstraint(
            "time",
            "currency_id",
            "timeframe_id",
            "period",
            "calc_version",
        ),
    )

    time = Column(DateTime, nullable=False)
    currency_id = Column(Integer, ForeignKey("dim_currency.id"), nullable=False)
    timeframe_id = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    calc_version = Column(Text, nullable=False)
    value = Column(Float)
    calculated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
