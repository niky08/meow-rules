#!/usr/bin/env python3
"""Rebuild meow-rules v1.6: isolate grok/x.ai, add xai-ipv4, clean direct-set."""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/root/meow-rules")
SB = Path(
    "/root/.cache/go-build/d3/d3bd058cf0be20b8f0a461563915c7259f5df6b15f4ea60f60e0383d4b37359e-d/sing-box"
)
DEC = ROOT / "decompiled"
ARCH = ROOT / "archive-grok-xai"

GROK_XAI_REMOVE_FROM_DIRECT = {"x.ai", "grok.x.com"}

ARCHIVE_FILES = [
    "grok-voice-ipv6.json",
    "grok-voice-ipv6.srs",
    "xai-ipv6.json",
    "xai-ipv6.srs",
]

COMPILE_MAP = {
    "ai-ipv6.json": "ai-ipv6.srs",
    "block.json": "block.srs",
    "doh-block.json": "doh-block.srs",
    "proxy.json": "proxy.srs",
    "youtube.json": "youtube.srs",
    "youtube-ipv4.json": "youtube-ipv4.srs",
    "youtube-ipv6.json": "youtube-ipv6.srs",
    "xai-ipv4.json": "xai-ipv4.srs",
    "direct.json": "direct.srs",
}

# Prefer existing source JSON; fall back to decompiled exports.
DECOMPILED_FALLBACK = ["block.json", "proxy.json"]


def compile_json(name: str, out: str) -> None:
    src = ROOT / name
    dst = ROOT / out
    subprocess.run([str(SB), "rule-set", "compile", str(src), "-o", str(dst)], check=True)
    print(f"compiled {name} -> {out}")


def clean_direct() -> None:
    src = DEC / "direct.json"
    with src.open() as f:
        data = json.load(f)
    rule = data["rules"][0]
    removed = 0
    for field in ("domain", "domain_suffix", "domain_keyword"):
        if field not in rule:
            continue
        before = len(rule[field])
        rule[field] = [d for d in rule[field] if d not in GROK_XAI_REMOVE_FROM_DIRECT]
        removed += before - len(rule[field])
    out = ROOT / "direct.json"
    with out.open("w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"direct.json: removed {removed} grok/x.ai domains ({', '.join(sorted(GROK_XAI_REMOVE_FROM_DIRECT))})")


def main() -> None:
    ARCH.mkdir(exist_ok=True)
    for name in ARCHIVE_FILES:
        src = ROOT / name
        if src.exists():
            shutil.move(str(src), str(ARCH / name))
            print(f"archived {name}")

    # keep decompiled copies for reference
    for name in ("grok-voice-ipv6.json", "xai-ipv6.json"):
        src = DEC / name
        if src.exists():
            shutil.copy2(src, ARCH / f"decompiled-{name}")

    clean_direct()

    for name in DECOMPILED_FALLBACK:
        src = ROOT / name
        if not src.exists():
            shutil.copy2(DEC / name, src)
            print(f"copied decompiled/{name}")

    for name, out in COMPILE_MAP.items():
        compile_json(name, out)

    print("done")


if __name__ == "__main__":
    main()