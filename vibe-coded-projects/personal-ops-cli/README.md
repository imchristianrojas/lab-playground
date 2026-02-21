# Personal Ops CLI

A practical local command-line tool for personal productivity workflows:

- Quick notes
- Task tracking
- Focus timer status

## Why this project

This is a good learning project because it covers:

- CLI design (`argparse`)
- JSON file persistence
- Date/time handling
- Simple architecture you can extend

## Quick Start

1. Create and activate a virtual environment (optional).
2. Install in editable mode (recommended when package index access is available):

```powershell
pip install -e .
```

If you are offline, use:

```powershell
$env:PYTHONPATH="src"
```

3. Run:

```powershell
ops note add "Read 10 pages" --tags learning,reading
ops note list

ops todo add "Ship CLI MVP" --due 2026-03-01
ops todo list --open
ops todo done 1

ops timer start "Deep work" --minutes 50
ops timer status
```

Offline alternative:

```powershell
python -m personal_ops_cli.cli note list
```

## Data Storage

Data is saved locally to:

`./data/ops_data.json`

## MVP Commands

- `note add`, `note list`
- `todo add`, `todo list`, `todo done`
- `timer start`, `timer status`

## Suggested Next Iterations

1. Add recurring tasks and priorities.
2. Add `export` commands for CSV/Markdown.
3. Add reminder notifications.
4. Package as `ops` executable via `pyproject.toml`.
5. Add tests for edge cases and command output formatting.
