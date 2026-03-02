"""Field validation and warning generation."""

from __future__ import annotations

import re

from contracts.models import ExtractedFields


def validate_fields(fields: ExtractedFields) -> list[str]:
    """
    Validate extracted fields and return a list of warnings.
    Does not modify the fields — only reports issues.
    """
    warnings: list[str] = []

    # Check GPA range
    if fields.gpa_requirement:
        nums = re.findall(r"(\d+\.?\d*)", fields.gpa_requirement)
        for n in nums:
            val = float(n)
            if val > 4.0 and val < 10:
                warnings.append(f"GPA value {val} seems unusual (not on 4.0 scale?)")

    # Check language score ranges
    if fields.language_requirement:
        ielts = re.findall(r"IELTS\s*(\d+\.?\d*)", fields.language_requirement, re.I)
        for score in ielts:
            val = float(score)
            if val > 9.0 or val < 4.0:
                warnings.append(f"IELTS score {val} out of valid range [0-9]")

        toefl = re.findall(r"TOEFL\s*(\d+)", fields.language_requirement, re.I)
        for score in toefl:
            val = int(score)
            if val > 120 or val < 40:
                warnings.append(f"TOEFL score {val} out of typical range [40-120]")

    # Check for empty critical fields
    critical = ["language_requirement", "deadlines"]
    for fname in critical:
        if getattr(fields, fname) is None:
            warnings.append(f"Field '{fname}' is empty — may need manual review")

    return warnings
