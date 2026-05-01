"""Download ServiceTitan OpenAPI specs for each API module.

Usage:
    python scripts/fetch_openapi.py

Writes one JSON file per module to docs/openapi/.
After running, use inspect_timestamps.py to identify which datetime fields
are UTC vs tenant-local.
"""

import json
import pathlib
import sys

try:
    import httpx
except ImportError:
    print("httpx not found — run: pip install httpx")
    sys.exit(1)

# ServiceTitan publishes one Swagger doc per module at this pattern.
# Adjust version suffix if ST publishes v3+ in future.
MODULES = {
    "jpm":        "https://developer.servicetitan.io/swagger/docs/jpmv2",
    "crm":        "https://developer.servicetitan.io/swagger/docs/crmv2",
    "dispatch":   "https://developer.servicetitan.io/swagger/docs/dispatchv2",
    "settings":   "https://developer.servicetitan.io/swagger/docs/settingsv2",
    "accounting": "https://developer.servicetitan.io/swagger/docs/accountingv2",
    "memberships":"https://developer.servicetitan.io/swagger/docs/membershipsv2",
    "pricebook":  "https://developer.servicetitan.io/swagger/docs/pricebookv2",
    "marketing":  "https://developer.servicetitan.io/swagger/docs/marketingv2",
}

OUT = pathlib.Path(__file__).parent.parent / "docs" / "openapi"
OUT.mkdir(parents=True, exist_ok=True)


def fetch_all() -> None:
    ok, failed = [], []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for module, url in MODULES.items():
            try:
                r = client.get(url)
                if r.status_code == 200:
                    spec = r.json()
                    out_path = OUT / f"{module}.json"
                    out_path.write_text(json.dumps(spec, indent=2))
                    path_count = len(spec.get("paths", {}))
                    print(f"  ✓  {module:<12} {path_count} paths  →  {out_path}")
                    ok.append(module)
                else:
                    print(f"  ✗  {module:<12} HTTP {r.status_code}  ({url})")
                    failed.append(module)
            except Exception as e:
                print(f"  ✗  {module:<12} {e}")
                failed.append(module)

    print(f"\n{len(ok)} succeeded, {len(failed)} failed.")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        print("These modules may require authentication or use a different URL pattern.")
        print("Check https://developer.servicetitan.io/apis/ for the correct spec URLs.")


def summarize_timestamps() -> None:
    """Print every dateTime field found across all downloaded specs, with its description."""
    print("\nDateTime fields found in downloaded specs:")
    print("=" * 70)
    for spec_file in sorted(OUT.glob("*.json")):
        spec = json.loads(spec_file.read_text())
        module = spec_file.stem
        definitions = spec.get("definitions", spec.get("components", {}).get("schemas", {}))
        for model_name, model in definitions.items():
            props = model.get("properties", {})
            for field, schema in props.items():
                if schema.get("format") == "date-time":
                    desc = schema.get("description", "").strip()
                    utc_hint = " ← UTC" if "utc" in desc.lower() else ""
                    local_hint = " ← LOCAL" if any(w in desc.lower() for w in ["local", "tenant", "timezone"]) else ""
                    print(f"  [{module}] {model_name}.{field}{utc_hint}{local_hint}")
                    if desc:
                        print(f"           {desc[:100]}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch ServiceTitan OpenAPI specs")
    parser.add_argument("--summarize", action="store_true", help="Summarize datetime fields from already-downloaded specs")
    args = parser.parse_args()

    if args.summarize:
        summarize_timestamps()
    else:
        print("Fetching ServiceTitan OpenAPI specs...\n")
        fetch_all()
        print("\nRun with --summarize to inspect datetime fields across all specs.")
