from datetime import date, datetime

from src.domain.recorrencia import first_due_date


def test_first_due_date_falls_back_to_today():
    assert first_due_date(None, 5, None, date(2026, 12, 21)) == date(2027, 1, 5)


def test_explicit_start_takes_precedence_over_creation():
    assert first_due_date(date(2026, 10, 5), 5, datetime(2026, 11, 1), date(2026, 9, 21)) == date(2026, 10, 5)
