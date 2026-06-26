#!/usr/bin/env python3
"""Rebuild meow-rules v1.6.1: purge ai-ipv6 overlaps from direct-set."""
import json
import subprocess
from pathlib import Path

ROOT = Path("/root/meow-rules")
SB = Path(
    "/root/.cache/go-build/d3/d3bd058cf0be20b8f0a461563915c7259f5df6b15f4ea60f60e0383d4b37359e-d/sing-box"
)
DEC = ROOT / "decompiled"

GROK_XAI_REMOVE = {"x.ai", "grok.x.com"}


def load_ai_targets() -> tuple[set[str], set[str], set[str]]:
    ai = json.load(open(ROOT / "ai-ipv6.json"))["rules"][0]
    domains = set(ai.get("domain", []))
    suffixes = set(ai.get("domain_suffix", []))
    keywords = set(ai.get("domain_keyword", []))
    for s in list(suffixes):
        suffixes.add(s.lstrip("."))
    return domains, suffixes, keywords


def matches_ai(value: str, field: str, domains: set[str], suffixes: set[str], keywords: set[str]) -> bool:
    if field == "domain":
        return value in domains
    if field == "domain_suffix":
        if value in suffixes:
            return True
        v = value.lstrip(".")
        return v in domains or any(value.endswith(s) or value.endswith(s.lstrip(".")) for s in suffixes)
    if field == "domain_keyword":
        if value in keywords:
            return True
        return any(k in value for k in keywords)
    return False


def clean_direct() -> None:
    domains, suffixes, keywords = load_ai_targets()
    with open(DEC / "direct.json") as f:
        data = json.load(f)
    rule = data["rules"][0]
    removed = {"domain": 0, "domain_suffix": 0, "domain_keyword": 0}

    for field in ("domain", "domain_suffix", "domain_keyword"):
        if field not in rule:
            continue
        kept = []
        for item in rule[field]:
            if item in GROK_XAI_REMOVE or matches_ai(item, field, domains, suffixes, keywords):
                removed[field] += 1
            else:
                kept.append(item)
        rule[field] = kept

    out = ROOT / "direct.json"
    with open(out, "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    total = sum(removed.values())
    print(f"direct.json: removed {total} entries ({removed})")


def main() -> None:
    clean_direct()
    subprocess.run(
        [str(SB), "rule-set", "compile", str(ROOT / "direct.json"), "-o", str(ROOT / "direct.srs")],
        check=True,
    )
    print("compiled direct.json -> direct.srs")
    print("done")


if __name__ == "__main__":
    main()