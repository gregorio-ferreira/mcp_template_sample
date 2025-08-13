#!/usr/bin/env python3
"""
Emplifi Listening API helper

- Auth: Basic (token:secret -> Base64) or pass the already encoded string.
- Endpoints used:
  * GET  /3/listening/queries         -> list all listening queries visible to the user.
  * POST /3/listening/posts           -> fetch content for queries; follows cursor pagination.

CLI subcommands
---------------
list-queries  : Lists queries, prints table, and/or writes CSV/Parquet/JSON.
posts         : Fetches listening posts for a date range + query IDs. Saves DataFrame.

Examples
--------
# List queries
python emplifi_listening.py list-queries \
  --auth-basic "<BASE64_TOKEN_SECRET>" \
  --out-csv listening_queries.csv

# Or build Basic auth from token+secret
python emplifi_listening.py list-queries --token YOUR_TOKEN --secret YOUR_SECRET

# Fetch posts
python emplifi_listening.py posts \
  --date-start 2025-07-13T18:49:40 \
  --date-end   2025-08-12T18:49:40 \
  --query-id   LNQ_1140092_66fe2dcd3e9eb298096e8db3 \
  --sort-field created_time --sort-order desc \
  --limit 100 \
  --out-parquet posts.parquet

Notes
-----
- For Basic auth: Authorization: Basic <base64(token:secret)>. Do NOT prefix the base64 with "Basic " when passing via --auth-basic (the code adds it).
- The /3/listening/posts endpoint uses cursor pagination via `data.next`. We keep calling with {"next": "<cursor>"} until exhaustion.
"""

import argparse
import base64
import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from pandas import json_normalize

BASE_URL = os.getenv("EMPLIFI_API_BASE", "https://api.emplifi.io/3")
DEFAULT_TIMEOUT = int(os.getenv("EMPLIFI_TIMEOUT", "30"))  # seconds


# ------------------------
# auth helpers
# ------------------------

def build_auth_header(auth_basic: Optional[str], token: Optional[str], secret: Optional[str]) -> Dict[str, str]:
    """Return {"Authorization": "Basic <base64>"}.

    You may pass --auth-basic directly (already base64 of token:secret),
    or provide --token and --secret to be encoded here.
    """
    if auth_basic:
        encoded = auth_basic.strip()
    else:
        if not token or not secret:
            raise SystemExit("Provide either --auth-basic OR both --token and --secret.")
        encoded = base64.b64encode(f"{token}:{secret}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


# ------------------------
# list listening queries
# ------------------------

def list_listening_queries(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """GET /3/listening/queries and return a list of query dicts.

    We handle a couple of possible shapes:
    - {"success": true, "data": [ ... ]}
    - {"data": [ ... ]}
    - Fallback: entire JSON if neither is present.
    """
    url = f"{BASE_URL}/listening/queries"
    resp = requests.get(
        url,
        headers={"Content-Type": "application/json", **headers},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()

    # Prefer `data` array if present
    data = body.get("data")
    if isinstance(data, list):
        return data

    # Some endpoints occasionally return top-level arrays or differently named keys
    if isinstance(body, list):
        return body

    # Try a generic key
    if "queries" in body and isinstance(body["queries"], list):
        return body["queries"]

    # Fallback: wrap body in a list
    return [body]


def list_queries_dataframe(headers: Dict[str, str]) -> pd.DataFrame:
    """Return the listening queries as a flattened pandas DataFrame."""
    items = list_listening_queries(headers)
    if not items:
        return pd.DataFrame()
    return json_normalize(items, max_level=1)


# ------------------------
# listening posts (with pagination)
# ------------------------

def fetch_all_posts(
    headers: Dict[str, str],
    date_start: str,
    date_end: str,
    listening_queries: List[str],
    fields: Optional[List[str]],
    sort_field: Optional[str],
    sort_order: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """POST /3/listening/posts and follow cursor pagination via `data.next`."""
    url = f"{BASE_URL}/listening/posts"
    common_headers = {
        "Content-Type": "application/json",
        **headers,
    }

    payload: Dict[str, Any] = {
        "date_start": date_start,
        "date_end": date_end,
        "listening_queries": listening_queries,
        "limit": limit,
    }
    if fields:
        payload["fields"] = fields
    if sort_field:
        payload["sort"] = [{"field": sort_field, "order": sort_order}]

    all_posts: List[Dict[str, Any]] = []

    # first page
    resp = requests.post(url, headers=common_headers, json=payload, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    data_block = body.get("data") or {}
    posts = data_block.get("posts", [])
    all_posts.extend(posts)
    next_cursor = data_block.get("next")

    # subsequent pages
    while next_cursor:
        resp = requests.post(url, headers=common_headers, json={"next": next_cursor}, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        data_block = body.get("data") or {}
        posts = data_block.get("posts", [])
        all_posts.extend(posts)
        next_cursor = data_block.get("next")

    return all_posts


def posts_dataframe(posts: List[Dict[str, Any]]) -> pd.DataFrame:
    """Flatten nested structures (author, attachments, etc.) into columns."""
    if not posts:
        return pd.DataFrame()
    return json_normalize(posts, max_level=2)


# ------------------------
# CLI
# ------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Emplifi Listening helper (list queries & posts)")

    # Auth
    parser.add_argument("--auth-basic", help="Base64 for 'token:secret' (NO 'Basic ' prefix).")
    parser.add_argument("--token", help="Emplifi API token (if not using --auth-basic).")
    parser.add_argument("--secret", help="Emplifi API secret (if not using --auth-basic).")

    # Outputs (global)
    parser.add_argument("--out-csv", help="Write CSV to this path (optional).")
    parser.add_argument("--out-parquet", help="Write Parquet to this path (optional).")
    parser.add_argument("--out-json", help="Write raw JSON to this path (optional).")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-queries subcommand
    p_list = subparsers.add_parser("list-queries", help="GET /3/listening/queries")

    # posts subcommand
    p_posts = subparsers.add_parser("posts", help="POST /3/listening/posts (with pagination)")
    p_posts.add_argument("--date-start", required=True, help="ISO date-time, e.g., 2025-07-13T18:49:40")
    p_posts.add_argument("--date-end", required=True, help="ISO date-time, e.g., 2025-08-12T18:49:40")
    p_posts.add_argument("--query-id", action="append", required=True, help="Listening query ID. Repeatable.")
    p_posts.add_argument("--field", action="append", help="Optional field(s) to request.")
    p_posts.add_argument("--sort-field", default=None, help="Field to sort by (e.g., created_time).")
    p_posts.add_argument("--sort-order", choices=["asc", "desc"], default="desc")
    p_posts.add_argument("--limit", type=int, default=100, help="Page size (max 100).")

    args = parser.parse_args()

    # Build auth
    headers = build_auth_header(args.auth_basic, args.token, args.secret)

    try:
        if args.command == "list-queries":
            items = list_listening_queries(headers)

            # Save raw JSON (optional)
            if args.out_json:
                with open(args.out_json, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)

            df = list_queries_dataframe(headers)
            if args.out_csv:
                df.to_csv(args.out_csv, index=False)
            if args.out_parquet:
                df.to_parquet(args.out_parquet, index=False)

            # Console preview
            print(f"Listening queries: {len(df)}")
            if not df.empty:
                preview_cols = [c for c in ["id", "name", "status", "community_enabled"] if c in df.columns]
                print(df[preview_cols].head(20).to_string(index=False))

        elif args.command == "posts":
            posts = fetch_all_posts(
                headers=headers,
                date_start=args.date_start,
                date_end=args.date_end,
                listening_queries=args.query_id,
                fields=args.field,
                sort_field=args.sort_field,
                sort_order=args.sort_order,
                limit=args.limit,
            )

            # Save raw JSON (optional)
            if args.out_json:
                with open(args.out_json, "w", encoding="utf-8") as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)

            df = posts_dataframe(posts)
            if args.out_csv:
                df.to_csv(args.out_csv, index=False)
            if args.out_parquet:
                df.to_parquet(args.out_parquet, index=False)

            print(f"Fetched posts: {len(posts)}")
            if not df.empty:
                preview_cols = [c for c in ["id", "created_time", "platform", "author.name", "sentiment"] if c in df.columns]
                print(df[preview_cols].head(10).to_string(index=False))

    except requests.HTTPError as e:
        try:
            err = e.response.json()
            msg = json.dumps(err, indent=2)
        except Exception:
            msg = e.response.text if e.response is not None else str(e)
        raise SystemExit(f"HTTP {e.response.status_code if e.response else ''}: {msg}")
    except Exception as e:
        raise SystemExit(f"Error: {e}")


if __name__ == "__main__":
    main()
