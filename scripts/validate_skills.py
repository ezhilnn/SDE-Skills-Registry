#!/usr/bin/env python3
"""Structural validator for SDE agent skills.

Checks required sections, identity fields, and evaluation case files.
Does not certify engineering judgment.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

REQUIRED_HEADINGS = [
    "Identity",
    "Purpose",
    "Activation",
    "Inputs",
    "Preconditions",
    "Context Requirements",
    "Tool Requirements",
    "Permission Model",
    "Security Boundaries",
    "Execution Workflow",
    "Reasoning Strategy",
    "Failure Handling",
    "Stop Conditions",
    "Verification",
    "Output Contract",
    "Examples",
    "Evaluation Criteria",
]

IDENTITY_FIELDS = ["name", "version", "category", "maturity", "risk", "mode"]
ALLOWED_RISK = {"low", "medium", "high", "critical"}
ALLOWED_MODE = {"advisory", "assisted", "controlled-execution", "autonomous"}
ALLOWED_MATURITY = {"draft", "experimental", "production"}
PRODUCTION_STATUSES = {"CONFIRMED", "LIKELY", "UNCONFIRMED", "BLOCKED", "NOT_REPRODUCED", "NO_ISSUE_FOUND"}


def headings(text: str) -> set[str]:
    found = set()
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if m:
            found.add(m.group(1).strip())
    return found


def parse_identity(text: str) -> dict[str, str]:
    block = re.search(r"## Identity\s+```ya?ml\n(.*?)```", text, re.S)
    if not block:
        return {}
    data: dict[str, str] = {}
    for line in block.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def validate_skill(skill_md: Path) -> list[str]:
    errors: list[str] = []
    text = skill_md.read_text(encoding="utf-8")
    found = headings(text)

    for heading in REQUIRED_HEADINGS:
        if heading not in found:
            errors.append(f"{skill_md}: missing heading '{heading}'")

    if "Non-Activation" not in found and "Non-activation" not in found:
        errors.append(f"{skill_md}: missing heading 'Non-Activation'")

    identity = parse_identity(text)
    for field in IDENTITY_FIELDS:
        if field not in identity:
            errors.append(f"{skill_md}: identity missing '{field}'")

    if identity.get("risk", "").lower() not in ALLOWED_RISK:
        errors.append(f"{skill_md}: invalid risk '{identity.get('risk')}'")
    if identity.get("mode", "").lower() not in ALLOWED_MODE:
        errors.append(f"{skill_md}: invalid mode '{identity.get('mode')}'")
    if identity.get("maturity", "").lower() not in ALLOWED_MATURITY:
        errors.append(f"{skill_md}: invalid maturity '{identity.get('maturity')}'")

    if "Status:" not in text or "Remaining Uncertainty:" not in text:
        errors.append(f"{skill_md}: output contract markers missing")

    eval_path = skill_md.parent / "EVALUATION.md"
    if identity.get("maturity", "").lower() == "production" and not eval_path.exists():
        errors.append(f"{skill_md}: production skill missing EVALUATION.md")
    if eval_path.exists():
        eval_text = eval_path.read_text(encoding="utf-8")
        if "type:" not in eval_text or "expected_activation:" not in eval_text:
            errors.append(f"{eval_path}: evaluation cases are incomplete")
        if identity.get("maturity", "").lower() == "production":
            for status in ("activation", "rejection", "safety"):
                if f"type: {status}" not in eval_text:
                    errors.append(f"{eval_path}: production evaluation missing '{status}' case")

    return errors


def main() -> int:
    if not SKILLS.exists():
        print("skills/ directory missing", file=sys.stderr)
        return 2

    skill_files = sorted(p for p in SKILLS.glob("**/SKILL.md") if p.is_file())
    if not skill_files:
        print("no SKILL.md files found", file=sys.stderr)
        return 2

    errors: list[str] = []
    for path in skill_files:
        errors.extend(validate_skill(path))

    catalog = SKILLS / "CATALOG.md"
    if not catalog.exists():
        errors.append("skills/CATALOG.md missing")

    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"VALIDATION OK ({len(skill_files)} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
