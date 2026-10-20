#!/usr/bin/env python3
"""Call mihomo's external-controller REST API without a secret CLI argument."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("endpoint", help="API path, such as /version or /proxies")
    parser.add_argument("--controller", default=os.environ.get("MIHOMO_CONTROLLER", "http://127.0.0.1:9090"))
    parser.add_argument("--method", default="GET", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    parser.add_argument("--json", dest="payload", help="JSON request body")
    parser.add_argument("--query", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--path-part", action="append", default=[], help="URL-encoded component appended after endpoint")
    parser.add_argument("--suffix", default="", help="Literal API suffix, such as /delay")
    args = parser.parse_args()

    secret = os.environ.get("MIHOMO_SECRET")
    if not secret:
        parser.error("MIHOMO_SECRET must be set in the environment")
    if not args.endpoint.startswith("/") or args.suffix and not args.suffix.startswith("/"):
        parser.error("endpoint and --suffix must start with /")
    query = urllib.parse.parse_qsl("&".join(args.query), keep_blank_values=True)
    path = args.endpoint.rstrip("/")
    for part in args.path_part:
        path += "/" + urllib.parse.quote(part, safe="")
    path += args.suffix
    url = args.controller.rstrip("/") + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = args.payload.encode() if args.payload is not None else None
    headers = {"Authorization": f"Bearer {secret}", "Accept": "application/json"}
    if data is not None:
        try:
            json.loads(args.payload)
        except json.JSONDecodeError as exc:
            parser.error(f"--json is not valid JSON: {exc.msg}")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=args.method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            if body:
                print(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"mihomo API error: HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"mihomo API error: {exc.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
