from datetime import date, datetime
from zoneinfo import ZoneInfo


BUSINESS_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def business_today() -> date:
    """Retorna a data civil usada pelas regras financeiras do produto."""
    return datetime.now(BUSINESS_TIMEZONE).date()
