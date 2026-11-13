#!/usr/bin/env python3
"""Verify deployed Pages bytes and clinic counts against the just-built local artifacts.

A deployment result is NOT a research-run success or a fresh intake confirmation.
No patient information is sent or processed.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import time
from urllib.parse import urljoin

import requests


FILES = ("index.html", "report.json", "documents/primary-care-directory.docx",
         "documents/primary-care-directory.pdf")


def verify(base_url, site_dir, session=requests, attempts=6, pause=15):
    root = pathlib.Path(site_dir)
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    index = (root / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="clinic-data" type="application/json">(.*?)</script>', index, re.S)
    if not match:
        raise ValueError("Built website lacks embedded clinic-data JSON")
    embedded = json.loads(match.group(1))
    count = len(embedded["clinics"])
    if count != report["count"]:
        raise ValueError(f"Local site/report count mismatch: {count} vs {report['count']}")
    if embedded.get("generated_on") != report.get("generated_on"):
        raise ValueError("Local site/report generation dates differ")
    if not (root / FILES[2]).read_bytes().startswith(b"PK"):
        raise ValueError("Local Word document is not a DOCX/ZIP file")
    if not (root / FILES[3]).read_bytes().startswith(b"%PDF-"):
        raise ValueError("Local PDF has no PDF header")

    last_errors = []
    for attempt in range(attempts):
        errors = []
        for name in FILES:
            url = urljoin(base_url.rstrip("/") + "/", name)
            try:
                response = session.get(url, timeout=(8, 30), headers={"Cache-Control": "no-cache"})
                response.raise_for_status()
                remote = response.content
                local = (root / name).read_bytes()
                if hashlib.sha256(remote).digest() != hashlib.sha256(local).digest():
                    errors.append(f"{name}: deployed bytes differ from current build")
            except requests.RequestException as exc:
                errors.append(f"{name}: retrieval failed ({type(exc).__name__}: {exc})")
        if not errors:
            return {"verified": True, "files": len(FILES), "clinics": count,
                    "generated_on": report.get("generated_on")}
        last_errors = errors
        if attempt + 1 < attempts:
            time.sleep(pause)
    raise RuntimeError("Live publication verification FAILED: " + "; ".join(last_errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--site-dir", default="site")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--pause", type=int, default=15)
    args = parser.parse_args()
    try:
        result = verify(args.base_url, args.site_dir, attempts=args.attempts, pause=args.pause)
        print(json.dumps(result, indent=2))
        print("Deployment validated; this does NOT establish that scheduled research succeeded.")
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
