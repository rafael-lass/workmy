"""Calendário compartilhado de faturamento e previsão (vencimentos de 1 a 28)."""
from datetime import date, datetime


def next_month(value: date, due_day: int) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, due_day)
    return date(value.year, value.month + 1, due_day)


def first_due_date(
    start: date | None, due_day: int, created_at: datetime | None, today: date,
) -> date:
    effective_start = start or (created_at.date() if created_at else today)
    candidate = date(effective_start.year, effective_start.month, due_day)
    return candidate if candidate >= effective_start else next_month(candidate, due_day)
