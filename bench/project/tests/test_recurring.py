import datetime as dt

from budgetbook.models import RecurringItem
from budgetbook.recurring import forecast, monthly_cost, occurrences


def d(year, month, day):
    return dt.date(year, month, day)


def test_monthly_item_on_the_31st_falls_on_month_ends():
    item = RecurringItem("loan", -20000, "debt", "monthly", d(2024, 1, 31))
    assert occurrences(item, d(2024, 1, 1), d(2024, 4, 30)) == [
        d(2024, 1, 31), d(2024, 2, 29), d(2024, 3, 31), d(2024, 4, 30),
    ]


def test_weekly_item_steps_by_seven_days_and_respects_the_window():
    item = RecurringItem("market", -3000, "food", "weekly", d(2024, 3, 2))
    assert occurrences(item, d(2024, 3, 10), d(2024, 3, 31)) == [d(2024, 3, 16), d(2024, 3, 23), d(2024, 3, 30)]


def test_yearly_item_on_leap_day():
    item = RecurringItem("club", -12000, "leisure", "yearly", d(2024, 2, 29))
    assert occurrences(item, d(2024, 1, 1), d(2026, 12, 31)) == [d(2024, 2, 29), d(2025, 2, 28), d(2026, 2, 28)]


def test_end_date_is_included_and_stops_the_item():
    item = RecurringItem("course", -5000, "education", "monthly", d(2024, 1, 15), end=d(2024, 3, 15))
    assert occurrences(item, d(2024, 1, 1), d(2024, 12, 31)) == [d(2024, 1, 15), d(2024, 2, 15), d(2024, 3, 15)]


def test_forecast_orders_by_date_then_name_and_monthly_cost_is_a_rough_sum():
    rent = RecurringItem("rent", -90000, "housing", "monthly", d(2024, 1, 1))
    gym = RecurringItem("gym", -3000, "health", "monthly", d(2024, 1, 1))
    pay = RecurringItem("pay", 250000, "salary", "monthly", d(2024, 1, 25))
    entries = forecast([rent, pay, gym], d(2024, 3, 1), d(2024, 3, 31))
    assert [(e.date.day, e.name) for e in entries] == [(1, "gym"), (1, "rent"), (25, "pay")]
    assert monthly_cost([rent, gym, pay]) == 157000
