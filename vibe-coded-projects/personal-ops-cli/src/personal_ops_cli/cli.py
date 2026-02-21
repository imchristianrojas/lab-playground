from __future__ import annotations

import argparse
from datetime import datetime, timezone

from personal_ops_cli.storage import Store, parse_date, timer_end_time, utc_now_iso


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops",
        description=(
            "Personal Ops CLI: manage notes, tasks, and a focus timer from your terminal."
        ),
        epilog=(
            "Examples:\n"
            "  ops note add \"Read 10 pages\" --tags learning,reading\n"
            "  ops note list --tag learning\n"
            "  ops todo add \"Ship CLI MVP\" --due 2026-03-01\n"
            "  ops todo done 1\n"
            "  ops timer start \"Deep work\" --minutes 50\n"
            "  ops timer status\n\n"
            "Run 'ops <domain> --help' for domain-specific help."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="domain", required=True)

    note_parser = subparsers.add_parser(
        "note",
        help="Create and view notes",
        description="Create quick notes and optionally label them with tags.",
        epilog=(
            "Examples:\n"
            "  ops note add \"Call plumber\" --tags home,urgent\n"
            "  ops note list\n"
            "  ops note list --tag urgent"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    note_sub = note_parser.add_subparsers(dest="action", required=True)
    note_add = note_sub.add_parser(
        "add",
        help="Add a note",
        description="Save a note with optional tags.",
    )
    note_add.add_argument("text", help="Note text to save. Wrap in quotes if it has spaces.")
    note_add.add_argument(
        "--tags",
        default="",
        help="Optional comma-separated tags (example: --tags learning,reading).",
    )
    note_list = note_sub.add_parser(
        "list",
        help="List notes",
        description="Show saved notes, optionally filtered by one exact tag.",
    )
    note_list.add_argument(
        "--tag",
        default="",
        help="Show only notes that include this tag.",
    )

    todo_parser = subparsers.add_parser(
        "todo",
        help="Create and track tasks",
        description="Track tasks, due dates, and completion state.",
        epilog=(
            "Examples:\n"
            "  ops todo add \"Pay rent\" --due 2026-03-01\n"
            "  ops todo list --open\n"
            "  ops todo done 2"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    todo_sub = todo_parser.add_subparsers(dest="action", required=True)
    todo_add = todo_sub.add_parser(
        "add",
        help="Add a todo",
        description="Create a new task with an optional due date.",
    )
    todo_add.add_argument("text", help="Task text to save. Wrap in quotes if it has spaces.")
    todo_add.add_argument(
        "--due",
        help="Optional due date in YYYY-MM-DD format (example: --due 2026-03-01).",
    )
    todo_list = todo_sub.add_parser(
        "list",
        help="List todos",
        description="Show tasks. Use --open to hide completed items.",
    )
    todo_list.add_argument(
        "--open",
        action="store_true",
        dest="open_only",
        help="Show only open (not completed) tasks.",
    )
    todo_done = todo_sub.add_parser(
        "done",
        help="Mark todo done",
        description="Mark a task as completed by its numeric id.",
    )
    todo_done.add_argument(
        "id",
        type=int,
        help="Task id shown in 'ops todo list'.",
    )

    timer_parser = subparsers.add_parser(
        "timer",
        help="Start/check focus timer",
        description="Run a single active focus timer and check remaining time.",
        epilog=(
            "Examples:\n"
            "  ops timer start \"Deep work\" --minutes 50\n"
            "  ops timer status"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    timer_sub = timer_parser.add_subparsers(dest="action", required=True)
    timer_start = timer_sub.add_parser(
        "start",
        help="Start timer",
        description="Start or replace the current timer with a new one.",
    )
    timer_start.add_argument(
        "label",
        help="Short timer label (example: 'Deep work').",
    )
    timer_start.add_argument(
        "--minutes",
        type=int,
        required=True,
        help="Timer duration in whole minutes (must be > 0).",
    )
    timer_sub.add_parser(
        "status",
        help="Timer status",
        description="Show whether a timer is active and how much time is left.",
    )

    return parser


def _cmd_note(args: argparse.Namespace, store: Store) -> int:
    data = store.load()
    if args.action == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        data["counters"]["note_id"] += 1
        note = {
            "id": data["counters"]["note_id"],
            "text": args.text,
            "tags": tags,
            "created_at": utc_now_iso(),
        }
        data["notes"].append(note)
        store.save(data)
        print(f"Added note #{note['id']}")
        return 0

    notes = data["notes"]
    if args.tag:
        notes = [n for n in notes if args.tag in n.get("tags", [])]
    if not notes:
        print("No notes found.")
        return 0
    for n in notes:
        tags = ",".join(n.get("tags", [])) or "-"
        print(f"[{n['id']}] {n['text']} | tags={tags} | {n['created_at']}")
    return 0


def _cmd_todo(args: argparse.Namespace, store: Store) -> int:
    data = store.load()
    if args.action == "add":
        due = parse_date(args.due) if args.due else None
        data["counters"]["todo_id"] += 1
        todo = {
            "id": data["counters"]["todo_id"],
            "text": args.text,
            "due": due,
            "done": False,
            "created_at": utc_now_iso(),
            "completed_at": None,
        }
        data["todos"].append(todo)
        store.save(data)
        print(f"Added todo #{todo['id']}")
        return 0

    if args.action == "done":
        todo = next((t for t in data["todos"] if t["id"] == args.id), None)
        if not todo:
            print(f"Todo #{args.id} not found.")
            return 1
        if todo["done"]:
            print(f"Todo #{args.id} is already done.")
            return 0
        todo["done"] = True
        todo["completed_at"] = utc_now_iso()
        store.save(data)
        print(f"Completed todo #{args.id}")
        return 0

    todos = data["todos"]
    if args.open_only:
        todos = [t for t in todos if not t["done"]]
    if not todos:
        print("No todos found.")
        return 0
    for t in todos:
        status = "done" if t["done"] else "open"
        due = t["due"] or "-"
        print(f"[{t['id']}] ({status}) {t['text']} | due={due}")
    return 0


def _cmd_timer(args: argparse.Namespace, store: Store) -> int:
    data = store.load()
    if args.action == "start":
        if args.minutes <= 0:
            print("--minutes must be positive.")
            return 1
        data["timer"] = {
            "label": args.label,
            "minutes": args.minutes,
            "started_at": utc_now_iso(),
        }
        store.save(data)
        print(f"Started timer '{args.label}' for {args.minutes}m.")
        return 0

    timer = data.get("timer")
    if not timer:
        print("No active timer.")
        return 0
    end_at = timer_end_time(timer["started_at"], timer["minutes"])
    now = datetime.now(timezone.utc)
    remaining = end_at - now
    seconds = int(remaining.total_seconds())
    if seconds <= 0:
        print(f"Timer '{timer['label']}' finished.")
        return 0
    mins, secs = divmod(seconds, 60)
    print(f"Timer '{timer['label']}' has {mins:02d}:{secs:02d} remaining.")
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    store = Store()

    try:
        if args.domain == "note":
            return _cmd_note(args, store)
        if args.domain == "todo":
            return _cmd_todo(args, store)
        if args.domain == "timer":
            return _cmd_timer(args, store)
        parser.print_help()
        return 1
    except ValueError as exc:
        print(f"Input error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
