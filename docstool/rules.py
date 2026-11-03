"""
Style & Terminology Rules Dictionary.
Based on the Google Developer Documentation Style Guide and Microsoft Writing Style Guide.
"""

from typing import List, Dict, Any

DEFAULT_STYLE_RULES: List[Dict[str, Any]] = [
    # 1. Non-inclusive & biased language
    {
        "rule_id": "STYLE-INCLUSIVE-01",
        "category": "inclusivity",
        "pattern": r"\bwhitelist\b",
        "preferred_term": "allowlist",
        "explanation": "Use 'allowlist' instead of 'whitelist' for inclusive terminology.",
        "severity": "ERROR"
    },
    {
        "rule_id": "STYLE-INCLUSIVE-02",
        "category": "inclusivity",
        "pattern": r"\bblacklist\b",
        "preferred_term": "denylist / blocklist",
        "explanation": "Use 'denylist' or 'blocklist' instead of 'blacklist'.",
        "severity": "ERROR"
    },
    {
        "rule_id": "STYLE-INCLUSIVE-03",
        "category": "inclusivity",
        "pattern": r"\bmaster/slave\b",
        "preferred_term": "primary/replica",
        "explanation": "Use 'primary/replica' or 'source/worker' instead of 'master/slave'.",
        "severity": "ERROR"
    },

    # 2. Condescending & filler words
    {
        "rule_id": "STYLE-CLARITY-01",
        "category": "clarity",
        "pattern": r"\b(simply|easy|easily|just|obviously|clearly)\b",
        "preferred_term": "[remove word]",
        "explanation": "Avoid words like 'simply', 'easily', or 'obviously' - they can demean readers if they encounter difficulties.",
        "severity": "WARNING"
    },
    {
        "rule_id": "STYLE-CLARITY-02",
        "category": "clarity",
        "pattern": r"\bplease note\b",
        "preferred_term": "Note: / Remember that",
        "explanation": "Avoid conversational 'please note' in technical writing. Use a formal admonition or 'Note:'.",
        "severity": "INFO"
    },

    # 3. Latin abbreviations (Google style prefers plain English)
    {
        "rule_id": "STYLE-LATIN-01",
        "category": "style",
        "pattern": r"\be\.g\.\b",
        "preferred_term": "for example",
        "explanation": "Spell out 'for example' instead of using Latin abbreviation 'e.g.'.",
        "severity": "WARNING"
    },
    {
        "rule_id": "STYLE-LATIN-02",
        "category": "style",
        "pattern": r"\bi\.e\.\b",
        "preferred_term": "that is",
        "explanation": "Spell out 'that is' instead of using Latin abbreviation 'i.e.'.",
        "severity": "WARNING"
    },

    # 4. Action verbs & UX terminology
    {
        "rule_id": "STYLE-UX-01",
        "category": "terminology",
        "pattern": r"\bclick on\b",
        "preferred_term": "click",
        "explanation": "Use 'click' instead of 'click on'.",
        "severity": "INFO"
    },
    {
        "rule_id": "STYLE-UX-02",
        "category": "terminology",
        "pattern": r"\bin order to\b",
        "preferred_term": "to",
        "explanation": "Simplify 'in order to' to 'to' for concise, active sentences.",
        "severity": "INFO"
    },

    # 5. Heading casing & future promises
    {
        "rule_id": "STYLE-VOICE-01",
        "category": "voice",
        "pattern": r"\b(in the future|in a future release|coming soon)\b",
        "preferred_term": "[specify target version or roadmap milestone]",
        "explanation": "Avoid vague future statements. Specify exact version or omit forward-looking promises.",
        "severity": "WARNING"
    }
]
