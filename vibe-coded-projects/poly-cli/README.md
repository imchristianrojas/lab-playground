# poly-cli

Terminal dashboard for highest-volume Polymarket markets and 24h change.

## Run (Python)

```powershell
python .\polymarket_dashboard.py
```

## Run (Rust)

```powershell
cargo run --bin polymarket-dashboard
```

## Useful options

```powershell
# Top 50 markets
python .\polymarket_dashboard.py --top 50
cargo run --bin polymarket-dashboard -- --top 50

# Refresh every 20 seconds
python .\polymarket_dashboard.py --watch --interval 20
cargo run --bin polymarket-dashboard -- --watch --interval 20

# JSON output for pipelines
python .\polymarket_dashboard.py --top 30 --json
cargo run --bin polymarket-dashboard -- --top 30 --json

# Disable colors (if needed)
python .\polymarket_dashboard.py --no-color
cargo run --bin polymarket-dashboard -- --no-color
```

## Notes

- Data source: `https://gamma-api.polymarket.com/events`
- The script sorts markets by total lifetime volume and shows 24h volume plus 24h price change when provided by the API.
- ANSI colors are enabled by default for interactive terminals (Windows Terminal supported).
