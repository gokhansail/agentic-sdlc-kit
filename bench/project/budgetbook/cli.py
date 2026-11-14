"""Command line interface.

``main`` returns the exit code: 0 on success, 1 for an error the user can fix (shown as
``error: ...`` on stderr), 2 for wrong usage (reported by argparse).
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from typing import Callable, Sequence

from . import budgets as budget_ops
from . import installments
from .accounts import balances
from .config import load_settings
from .csvio import export_csv, import_csv
from .dates import month_bounds, parse_date, parse_month
from .errors import AmountError, BudgetbookError, DateError
from .filters import select
from .ledger import Ledger
from .models import FREQUENCIES, RecurringItem
from .money import format_amount, parse_amount
from .recurring import forecast
from .rendering import (
    render_balances,
    render_budget_list,
    render_comparison,
    render_forecast,
    render_report,
    render_summary,
    render_top,
    render_transactions,
)
from .reports import monthly_report
from .stats import compare_with_previous_month, top_categories
from .summary import year_totals, yearly_summary


def _date_arg(text: str) -> dt.date:
    try:
        return parse_date(text)
    except DateError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _month_arg(text: str) -> tuple[int, int]:
    try:
        return parse_month(text)
    except DateError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _amount_arg(text: str) -> int:
    try:
        return parse_amount(text)
    except AmountError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budgetbook", description="A small household budget ledger.")
    parser.add_argument("--data", help="ledger file (default: BUDGETBOOK_DATA_FILE or budgetbook.json)")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="book a transaction")
    add.add_argument("date", type=_date_arg)
    add.add_argument("amount", type=_amount_arg, help="negative for an expense")
    add.add_argument("category")
    add.add_argument("description", nargs="?", default="")
    add.add_argument("--account", default="main")
    add.set_defaults(handler=_cmd_add)

    lst = commands.add_parser("list", help="list transactions")
    lst.add_argument("--from", dest="from_date", type=_date_arg, help="first day, included")
    lst.add_argument("--to", dest="to_date", type=_date_arg, help="last day, included")
    lst.add_argument("--category", help="a category and everything below it")
    lst.add_argument("--account")
    lst.add_argument("--search", help="text in description or category")
    lst.set_defaults(handler=_cmd_list)

    edit = commands.add_parser("edit", help="change fields of a transaction")
    edit.add_argument("id", type=int)
    edit.add_argument("--date", type=_date_arg)
    edit.add_argument("--amount", type=_amount_arg)
    edit.add_argument("--category")
    edit.add_argument("--description")
    edit.add_argument("--account")
    edit.set_defaults(handler=_cmd_edit)

    remove = commands.add_parser("remove", help="delete a transaction by id")
    remove.add_argument("id", type=int)
    remove.set_defaults(handler=_cmd_remove)

    report = commands.add_parser("report", help="monthly report")
    report.add_argument("month", type=_month_arg, help="YYYY-MM")
    report.set_defaults(handler=_cmd_report)

    summary = commands.add_parser("summary", help="income and expenses for each month of a year")
    summary.add_argument("year", type=int)
    summary.set_defaults(handler=_cmd_summary)

    accounts = commands.add_parser("accounts", help="balance per account")
    accounts.add_argument("--as-of", type=_date_arg)
    accounts.set_defaults(handler=_cmd_accounts)

    top = commands.add_parser("top", help="the top-level categories with the highest expenses in a month")
    top.add_argument("month", type=_month_arg, help="YYYY-MM")
    top.add_argument("--count", type=int, default=5)
    top.set_defaults(handler=_cmd_top)

    compare = commands.add_parser("compare", help="expenses of a month against the month before")
    compare.add_argument("month", type=_month_arg, help="YYYY-MM")
    compare.set_defaults(handler=_cmd_compare)

    inst = commands.add_parser("installments", help="book a purchase paid in monthly parts")
    inst.add_argument("total", type=_amount_arg, help="the whole amount, positive")
    inst.add_argument("parts", type=int)
    inst.add_argument("first", type=_date_arg, help="date of the first part")
    inst.add_argument("category")
    inst.add_argument("description", nargs="?", default="")
    inst.add_argument("--account", default="main")
    inst.set_defaults(handler=_cmd_installments)

    imp = commands.add_parser("import", help="import transactions from a CSV file")
    imp.add_argument("file")
    imp.add_argument("--skip-duplicates", action="store_true", help="leave out rows that are already booked")
    imp.set_defaults(handler=_cmd_import)

    exp = commands.add_parser("export", help="write transactions to a CSV file (- for stdout)")
    exp.add_argument("file")
    exp.add_argument("--from", dest="from_date", type=_date_arg)
    exp.add_argument("--to", dest="to_date", type=_date_arg)
    exp.set_defaults(handler=_cmd_export)

    recurring = commands.add_parser("recurring", help="recurring payments and income")
    rec_commands = recurring.add_subparsers(dest="recurring_command", required=True)
    rec_add = rec_commands.add_parser("add")
    rec_add.add_argument("name")
    rec_add.add_argument("amount", type=_amount_arg)
    rec_add.add_argument("category")
    rec_add.add_argument("frequency", choices=FREQUENCIES)
    rec_add.add_argument("start", type=_date_arg)
    rec_add.add_argument("--end", type=_date_arg)
    rec_add.add_argument("--account", default="main")
    rec_add.set_defaults(handler=_cmd_recurring_add)
    rec_list = rec_commands.add_parser("list")
    rec_list.set_defaults(handler=_cmd_recurring_list)

    fc = commands.add_parser("forecast", help="expected recurring bookings in a month")
    fc.add_argument("month", type=_month_arg, help="YYYY-MM")
    fc.set_defaults(handler=_cmd_forecast)

    budget = commands.add_parser("budget", help="monthly budgets per category")
    budget_commands = budget.add_subparsers(dest="budget_command", required=True)
    b_set = budget_commands.add_parser("set")
    b_set.add_argument("category")
    b_set.add_argument("limit", type=_amount_arg)
    b_set.set_defaults(handler=_cmd_budget_set)
    b_list = budget_commands.add_parser("list")
    b_list.set_defaults(handler=_cmd_budget_list)
    b_remove = budget_commands.add_parser("remove")
    b_remove.add_argument("category")
    b_remove.set_defaults(handler=_cmd_budget_remove)
    return parser


# -- handlers: each loads the ledger, does its work, saves when it changed something -------


def _cmd_add(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    tx = ledger.add(args.date, args.amount, args.category, args.description, args.account)
    ledger.save(path)
    print(f"Added {tx.id}: {tx.date.isoformat()} {format_amount(tx.amount)} {tx.category}")
    return 0


def _cmd_list(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    transactions = ledger.between(args.from_date, args.to_date)
    transactions = select(transactions, category=args.category, account=args.account, text=args.search)
    print(render_transactions(transactions))
    return 0


def _cmd_edit(args: argparse.Namespace, path: str) -> int:
    changes = {
        name: getattr(args, name)
        for name in ("date", "amount", "category", "description", "account")
        if getattr(args, name) is not None
    }
    if not changes:
        raise BudgetbookError("nothing to change; give at least one of --date, --amount, --category, --description, --account")
    ledger = Ledger.load(path)
    tx = ledger.update(args.id, **changes)
    ledger.save(path)
    print(f"Updated {tx.id}: {tx.date.isoformat()} {format_amount(tx.amount)} {tx.category}")
    return 0


def _cmd_top(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    year, month = args.month
    ranked = top_categories(ledger.in_month(year, month), args.count)
    print(render_top(ranked))
    return 0


def _cmd_remove(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    tx = ledger.remove(args.id)
    ledger.save(path)
    print(f"Removed {tx.id}: {tx.date.isoformat()} {tx.category}")
    return 0


def _cmd_report(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    year, month = args.month
    print(render_report(monthly_report(ledger, year, month)))
    return 0


def _cmd_summary(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    lines = yearly_summary(ledger, args.year)
    print(render_summary(args.year, lines, year_totals(lines)))
    return 0


def _cmd_compare(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    year, month = args.month
    print(render_comparison(compare_with_previous_month(ledger, year, month)))
    return 0


def _cmd_installments(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    try:
        booked = installments.book(
            ledger, args.total, args.parts, args.first, args.category, args.description, args.account
        )
    except ValueError as exc:
        raise BudgetbookError(str(exc)) from None
    ledger.save(path)
    print(f"Booked {len(booked)} installments, ids {booked[0].id} to {booked[-1].id}.")
    return 0


def _cmd_accounts(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    print(render_balances(balances(ledger, args.as_of)))
    return 0


def _cmd_import(args: argparse.Namespace, path: str) -> int:
    try:
        with open(args.file, encoding="utf-8", newline="") as handle:
            text = handle.read()
    except OSError as exc:
        raise BudgetbookError(f"cannot read {args.file}: {exc.strerror}") from None
    ledger = Ledger.load(path)
    count = import_csv(ledger, text, skip_duplicates=args.skip_duplicates)
    ledger.save(path)
    print(f"Imported {count} transaction{'s' if count != 1 else ''}.")
    return 0


def _cmd_export(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    text = export_csv(ledger.between(args.from_date, args.to_date))
    if args.file == "-":
        sys.stdout.write(text)
        return 0
    try:
        with open(args.file, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except OSError as exc:
        raise BudgetbookError(f"cannot write {args.file}: {exc.strerror}") from None
    print(f"Exported to {args.file}.")
    return 0


def _cmd_recurring_add(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    try:
        item = RecurringItem(
            args.name, args.amount, args.category, args.frequency, args.start, args.end, args.account
        )
    except ValueError as exc:
        raise BudgetbookError(str(exc)) from None
    ledger.recurring.append(item)
    ledger.save(path)
    print(f"Added recurring item {item.name}.")
    return 0


def _cmd_recurring_list(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    if not ledger.recurring:
        print("No recurring items.")
        return 0
    for item in ledger.recurring:
        until = f" until {item.end.isoformat()}" if item.end else ""
        print(f"{item.name}: {format_amount(item.amount)} {item.frequency} from {item.start.isoformat()}{until}")
    return 0


def _cmd_forecast(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    year, month = args.month
    first, last = month_bounds(year, month)
    print(render_forecast(year, month, forecast(ledger.recurring, first, last)))
    return 0


def _cmd_budget_set(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    name = budget_ops.set_budget(ledger, args.category, args.limit)
    ledger.save(path)
    print(f"Budget for {name} set.")
    return 0


def _cmd_budget_list(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    print(render_budget_list(budget_ops.all_budgets(ledger)))
    return 0


def _cmd_budget_remove(args: argparse.Namespace, path: str) -> int:
    ledger = Ledger.load(path)
    budget_ops.remove_budget(ledger, args.category)
    ledger.save(path)
    print(f"Budget for {args.category} removed.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = args.data or load_settings().data_file
    handler: Callable[[argparse.Namespace, str], int] = args.handler
    try:
        return handler(args, path)
    except BudgetbookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
