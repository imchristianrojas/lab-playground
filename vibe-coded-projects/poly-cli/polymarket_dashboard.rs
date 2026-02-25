use std::cmp::Ordering;
use std::env;
use std::io::{self, Write};
use std::thread;
use std::time::Duration;

use chrono::{DateTime, Utc};
use clap::Parser;
use regex::Regex;
use reqwest::blocking::Client;
use reqwest::header::{ACCEPT, USER_AGENT};
use serde::Serialize;
use serde_json::Value;

const BASE_URL: &str = "https://gamma-api.polymarket.com/events";

#[derive(Parser, Debug)]
#[command(about = "Polymarket dashboard: highest volume markets + 24h change")]
struct Args {
    #[arg(long, default_value_t = 20, help = "Number of markets to display")]
    top: usize,

    #[arg(
        long = "fetch-limit",
        default_value_t = 150,
        help = "Number of events to fetch from API (higher = broader coverage)"
    )]
    fetch_limit: usize,

    #[arg(long, help = "Continuously refresh the dashboard")]
    watch: bool,

    #[arg(long, default_value_t = 30, help = "Refresh interval seconds in watch mode")]
    interval: u64,

    #[arg(long, help = "Emit top markets as JSON (for pipelines)")]
    json: bool,

    #[arg(long = "no-color", help = "Disable ANSI colors in terminal output")]
    no_color: bool,
}

#[derive(Debug, Clone, Serialize)]
struct Row {
    event: String,
    title: String,
    slug: Option<String>,
    volume: f64,
    #[serde(rename = "volume24h")]
    volume_24h: f64,
    #[serde(rename = "change24hPct")]
    change_24h_pct: Option<f64>,
    #[serde(rename = "endDate")]
    end_date: Option<String>,
}

struct C;
impl C {
    const RESET: &'static str = "\x1b[0m";
    const BOLD: &'static str = "\x1b[1m";
    const DIM: &'static str = "\x1b[2m";
    const CYAN: &'static str = "\x1b[36m";
    const BLUE: &'static str = "\x1b[94m";
    const GREEN: &'static str = "\x1b[92m";
    const RED: &'static str = "\x1b[91m";
    const YELLOW: &'static str = "\x1b[93m";
    const WHITE: &'static str = "\x1b[97m";
}

fn supports_color(no_color: bool) -> bool {
    if no_color || env::var_os("NO_COLOR").is_some() {
        return false;
    }
    atty::is(atty::Stream::Stdout)
}

fn paint(text: &str, color: &str, enabled: bool) -> String {
    if !enabled {
        return text.to_string();
    }
    format!("{color}{text}{}", C::RESET)
}

fn as_f64(value: Option<&Value>, default: f64) -> f64 {
    match value {
        None => default,
        Some(v) => {
            if let Some(n) = v.as_f64() {
                n
            } else if let Some(n) = v.as_i64() {
                n as f64
            } else if let Some(s) = v.as_str() {
                s.trim().parse::<f64>().unwrap_or(default)
            } else {
                default
            }
        }
    }
}

fn normalize_change(raw: Option<&Value>) -> Option<f64> {
    let val = match raw {
        Some(v) if !v.is_null() => as_f64(Some(v), 0.0),
        _ => return None,
    };

    if (-1.0..=1.0).contains(&val) {
        Some(val * 100.0)
    } else {
        Some(val)
    }
}

fn format_money(value: f64) -> String {
    let abs_value = value.abs();
    if abs_value >= 1_000_000_000.0 {
        format!("${:.2}B", value / 1_000_000_000.0)
    } else if abs_value >= 1_000_000.0 {
        format!("${:.2}M", value / 1_000_000.0)
    } else if abs_value >= 1_000.0 {
        format!("${:.1}K", value / 1_000.0)
    } else {
        format!("${:.0}", value)
    }
}

fn format_percent(value: Option<f64>) -> String {
    match value {
        None => "n/a".to_string(),
        Some(v) if v > 0.0 => format!("+{v:.2}%"),
        Some(v) => format!("{v:.2}%"),
    }
}

fn visible_len(text: &str, ansi_re: &Regex) -> usize {
    ansi_re.replace_all(text, "").chars().count()
}

fn truncate_visible(text: &str, max_len: usize, ansi_re: &Regex) -> String {
    if max_len == 0 {
        return String::new();
    }
    if visible_len(text, ansi_re) <= max_len {
        return text.to_string();
    }

    let plain = ansi_re.replace_all(text, "");
    let mut out = String::new();
    let take = if max_len <= 3 { max_len } else { max_len - 3 };

    for ch in plain.chars().take(take) {
        out.push(ch);
    }

    if max_len > 3 {
        out.push_str("...");
    }

    out
}

fn pad_visible(text: &str, width: usize, ansi_re: &Regex) -> String {
    let truncated = truncate_visible(text, width, ansi_re);
    let len = visible_len(&truncated, ansi_re);
    if len >= width {
        truncated
    } else {
        format!("{}{}", truncated, " ".repeat(width - len))
    }
}

fn fetch_markets(limit: usize, offset: usize) -> Result<Vec<Row>, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(20))
        .build()
        .map_err(|e| format!("http client error: {e}"))?;

    let payload: Value = client
        .get(BASE_URL)
        .query(&[
            ("active", "true"),
            ("closed", "false"),
            ("order", "volume"),
            ("ascending", "false"),
            ("limit", &limit.to_string()),
            ("offset", &offset.to_string()),
        ])
        .header(USER_AGENT, "poly-cli-dashboard/1.0")
        .header(ACCEPT, "application/json")
        .send()
        .map_err(|e| format!("request error: {e}"))?
        .error_for_status()
        .map_err(|e| format!("http status error: {e}"))?
        .json()
        .map_err(|e| format!("json decode error: {e}"))?;

    let events = payload
        .as_array()
        .ok_or_else(|| "unexpected API response shape (expected array)".to_string())?;

    let mut rows = Vec::new();

    for event in events {
        let event_title = event
            .get("title")
            .and_then(Value::as_str)
            .or_else(|| event.get("slug").and_then(Value::as_str))
            .unwrap_or("Untitled Event")
            .to_string();

        let event_slug = event.get("slug").and_then(Value::as_str).map(str::to_string);

        let markets = event
            .get("markets")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();

        for market in markets {
            let title = market
                .get("question")
                .and_then(Value::as_str)
                .or_else(|| market.get("title").and_then(Value::as_str))
                .or_else(|| market.get("slug").and_then(Value::as_str))
                .unwrap_or(&event_title)
                .to_string();

            let total_volume = as_f64(
                market
                    .get("volumeNum")
                    .or_else(|| market.get("volume"))
                    .or_else(|| market.get("volumeClob"))
                    .or_else(|| market.get("volumeAmm")),
                0.0,
            );

            let volume_24h = as_f64(market.get("volume24hr"), 0.0);
            let change_24h_pct = normalize_change(
                market
                    .get("oneDayPriceChange")
                    .or_else(|| market.get("oneDayPriceChangePercent")),
            );

            let slug = market
                .get("slug")
                .and_then(Value::as_str)
                .map(str::to_string)
                .or_else(|| event_slug.clone());

            let end_date = market
                .get("endDateIso")
                .and_then(Value::as_str)
                .map(str::to_string)
                .or_else(|| {
                    market
                        .get("endDate")
                        .and_then(Value::as_str)
                        .map(str::to_string)
                });

            rows.push(Row {
                event: event_title.clone(),
                title,
                slug,
                volume: total_volume,
                volume_24h,
                change_24h_pct,
                end_date,
            });
        }
    }

    rows.sort_by(|a, b| match b.volume.partial_cmp(&a.volume) {
        Some(ord) => ord,
        None => Ordering::Equal,
    });

    Ok(rows)
}

fn render_table(rows: &[Row], top: usize, color: bool) -> String {
    let top_rows = &rows[..rows.len().min(top)];
    let headers = ["#", "Market", "Total Volume", "24h Volume", "24h Change", "End"];
    let widths = [4, 64, 14, 12, 11, 20];
    let ansi_re = Regex::new(r"\x1b\[[0-9;]*m").expect("valid ansi regex");

    let mut lines = Vec::new();

    let header_line = headers
        .iter()
        .enumerate()
        .map(|(i, h)| pad_visible(&paint(h, &(String::from(C::BLUE) + C::BOLD), color), widths[i], &ansi_re))
        .collect::<Vec<_>>()
        .join(" | ");
    lines.push(header_line);

    let divider_width = widths.iter().sum::<usize>() + (3 * (widths.len() - 1));
    lines.push(paint(&"-".repeat(divider_width), C::DIM, color));

    for (idx, row) in top_rows.iter().enumerate() {
        let end_str = row
            .end_date
            .as_ref()
            .and_then(|s| {
                DateTime::parse_from_rfc3339(s)
                    .ok()
                    .map(|dt| dt.format("%Y-%m-%d %H:%M").to_string())
                    .or_else(|| Some(s.clone()))
            })
            .unwrap_or_else(|| "n/a".to_string());

        let mut change_txt = format_percent(row.change_24h_pct);
        change_txt = match row.change_24h_pct {
            None => paint(&change_txt, C::DIM, color),
            Some(v) if v > 0.0 => paint(&format!("+ {change_txt}"), &(String::from(C::GREEN) + C::BOLD), color),
            Some(v) if v < 0.0 => paint(&format!("- {}", change_txt.trim_start_matches('-')), &(String::from(C::RED) + C::BOLD), color),
            Some(_) => paint(&change_txt, C::YELLOW, color),
        };

        let cols = vec![
            paint(&(idx + 1).to_string(), &(String::from(C::CYAN) + C::BOLD), color),
            paint(&row.title, C::WHITE, color),
            paint(&format_money(row.volume), C::CYAN, color),
            paint(&format_money(row.volume_24h), C::CYAN, color),
            change_txt,
            paint(&end_str, C::DIM, color),
        ];

        let line = cols
            .iter()
            .enumerate()
            .map(|(i, col)| pad_visible(col, widths[i], &ansi_re))
            .collect::<Vec<_>>()
            .join(" | ");

        lines.push(line);
    }

    lines.join("\n")
}

fn clear_screen() {
    #[cfg(windows)]
    {
        let _ = std::process::Command::new("cmd").args(["/C", "cls"]).status();
    }
    #[cfg(not(windows))]
    {
        print!("\x1B[2J\x1B[1;1H");
        let _ = io::stdout().flush();
    }
}

fn run(args: &Args) -> i32 {
    let color = supports_color(args.no_color);

    loop {
        let rows = match fetch_markets(args.fetch_limit.max(args.top), 0) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("Failed to fetch data: {e}");
                if args.watch {
                    thread::sleep(Duration::from_secs(args.interval));
                    continue;
                }
                return 1;
            }
        };

        if args.json {
            let top_rows = &rows[..rows.len().min(args.top)];
            match serde_json::to_string_pretty(top_rows) {
                Ok(s) => println!("{s}"),
                Err(e) => {
                    eprintln!("Failed to serialize JSON: {e}");
                    return 1;
                }
            }
        } else {
            clear_screen();
            let now = Utc::now().format("%Y-%m-%d %H:%M:%S UTC");
            let title = paint(
                &format!("Polymarket Top {} by Volume", args.top),
                &(String::from(C::BOLD) + C::CYAN),
                color,
            );
            let updated = paint(&format!("Updated: {now}"), C::DIM, color);

            println!("{title}  |  {updated}");
            println!("{}", render_table(&rows, args.top, color));
            println!(
                "{}",
                paint("\nSource: https://gamma-api.polymarket.com/events", C::DIM, color)
            );
        }

        if !args.watch || args.json {
            break;
        }

        thread::sleep(Duration::from_secs(args.interval));
    }

    0
}

fn main() {
    let args = Args::parse();

    if args.top < 1 {
        eprintln!("--top must be >= 1");
        std::process::exit(2);
    }
    if args.fetch_limit < 1 {
        eprintln!("--fetch-limit must be >= 1");
        std::process::exit(2);
    }
    if args.interval < 2 {
        eprintln!("--interval must be >= 2");
        std::process::exit(2);
    }

    std::process::exit(run(&args));
}
