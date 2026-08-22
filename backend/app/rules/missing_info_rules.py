"""
Missing Information Rules — Phase 8.

For each of the 10 predefined attention categories, this module defines:
  - STRONG patterns: multiple keywords whose co-presence suggests the topic is
    adequately addressed (→ PRESENT)
  - WEAK patterns: single-keyword hints that the topic may be mentioned but
    not clearly enough (→ UNCLEAR if only weak matches)
  - If no patterns match at all → NOT_IDENTIFIED

This is an information-completeness detector, NOT a legal compliance checker.
"PRESENT" means the document appears to address this topic.
"UNCLEAR" means something related is mentioned but lacks clarity.
"NOT_IDENTIFIED" means the topic could not be found at all.

NEVER:
- invent legal requirements
- declare anything illegal or unenforceable
- claim a missing clause makes the agreement invalid
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Status constants — only these three values are allowed
PRESENT = "PRESENT"
UNCLEAR = "UNCLEAR"
NOT_IDENTIFIED = "NOT_IDENTIFIED"

VALID_STATUSES = {PRESENT, UNCLEAR, NOT_IDENTIFIED}


@dataclass(frozen=True)
class MissingInfoRule:
    """
    Rule for one attention category's completeness check.

    strong_patterns: if ANY of these appears, the topic is considered PRESENT.
      These are specific, descriptive phrases that indicate the category is
      actually addressed.
    weak_patterns: if only these appear (no strong match), return UNCLEAR.
      These are vague or partial signals.
    not_found_explanation: shown when status is NOT_IDENTIFIED.
    unclear_explanation: shown when status is UNCLEAR.
    """
    category_id: str
    category_name: str
    strong_patterns: List[str]
    weak_patterns: List[str]
    not_found_explanation: str
    unclear_explanation: str


MISSING_INFO_RULES: List[MissingInfoRule] = [

    MissingInfoRule(
        category_id="SECURITY_DEPOSIT",
        category_name="Security Deposit",
        strong_patterns=[
            "security deposit",
            "refundable deposit",
            "caution deposit",
            "advance deposit",
            "deposit amount",
            "deposit of",
            "deposit shall be",
            "deposit refund",
            "deposit deduction",
        ],
        weak_patterns=[
            "deposit",
            "advance",
        ],
        not_found_explanation=(
            "No security deposit terms could be identified in this agreement. "
            "Consider clarifying whether a deposit is required and under what "
            "conditions it will be returned."
        ),
        unclear_explanation=(
            "The agreement appears to mention a deposit, but the terms are not "
            "clearly stated. Consider clarifying the amount, refund conditions, "
            "and any deduction terms."
        ),
    ),

    MissingInfoRule(
        category_id="NOTICE_PERIOD",
        category_name="Notice Period",
        strong_patterns=[
            "notice period",
            "days' notice",
            "days notice",
            "days of notice",
            "month's notice",
            "months notice",
            "termination notice",
            "written notice of",
            "give notice",
            "advance notice of",
        ],
        weak_patterns=[
            "notice",
            "inform",
            "notify",
        ],
        not_found_explanation=(
            "No notice period terms could be identified in this agreement. "
            "Consider clarifying how much advance notice is required from each party."
        ),
        unclear_explanation=(
            "A notice requirement appears to be mentioned, but the required duration "
            "or conditions are not clearly stated."
        ),
    ),

    MissingInfoRule(
        category_id="LOCK_IN_PERIOD",
        category_name="Lock-in Period",
        strong_patterns=[
            "lock-in period",
            "lock in period",
            "lockin period",
            "minimum stay",
            "minimum period",
            "minimum tenure",
            "cannot terminate before",
            "lock-in penalty",
            "lock in penalty",
            "early termination during lock",
        ],
        weak_patterns=[
            "lock",
            "minimum",
            "cannot leave",
        ],
        not_found_explanation=(
            "No lock-in or minimum stay period could be identified in this agreement. "
            "Consider clarifying whether there is a minimum tenancy requirement."
        ),
        unclear_explanation=(
            "The agreement may contain a lock-in period, but the duration or "
            "consequences of early exit are not clearly stated."
        ),
    ),

    MissingInfoRule(
        category_id="EARLY_TERMINATION",
        category_name="Early Termination",
        strong_patterns=[
            "early termination",
            "premature termination",
            "termination before expiry",
            "penalty for leaving early",
            "compensation for early termination",
            "terminate early",
            "exit before",
            "vacate before the expiry",
        ],
        weak_patterns=[
            "terminate",
            "vacate",
            "end the agreement",
            "forfeit",
        ],
        not_found_explanation=(
            "No early termination terms could be identified in this agreement. "
            "Consider clarifying what happens if either party ends the agreement "
            "before the scheduled end date."
        ),
        unclear_explanation=(
            "Termination appears to be mentioned, but the consequences or "
            "conditions for early exit are not clearly described."
        ),
    ),

    MissingInfoRule(
        category_id="MAINTENANCE_RESPONSIBILITY",
        category_name="Maintenance Responsibility",
        strong_patterns=[
            "tenant responsible for repairs",
            "tenant shall maintain",
            "tenant must maintain",
            "tenant is responsible",
            "repair costs",
            "appliance repair",
            "at tenant's cost",
            "at the tenant's expense",
            "landlord shall maintain",
            "landlord is responsible for",
            "owner shall be responsible",
        ],
        weak_patterns=[
            "maintenance",
            "repair",
            "upkeep",
            "plumbing",
            "electrical",
        ],
        not_found_explanation=(
            "No maintenance or repair responsibility terms could be identified "
            "in this agreement. Consider clarifying who is responsible for repairs "
            "and maintenance."
        ),
        unclear_explanation=(
            "Maintenance appears to be mentioned, but it is not clearly stated "
            "who is responsible for specific repairs or costs."
        ),
    ),

    MissingInfoRule(
        category_id="RENT_INCREASE",
        category_name="Rent Increase",
        strong_patterns=[
            "rent increase",
            "rent escalation",
            "annual increase",
            "rent revision",
            "percentage increase",
            "rent enhancement",
            "revised rent",
            "increment in rent",
            "increase in rent",
            "hike in rent",
        ],
        weak_patterns=[
            "increase",
            "revision",
            "escalation",
        ],
        not_found_explanation=(
            "No rent increase or escalation terms could be identified in this "
            "agreement. Consider clarifying whether and how the rent may change "
            "during the tenancy."
        ),
        unclear_explanation=(
            "A potential rent increase is mentioned, but the conditions, "
            "percentage, or timing are not clearly stated."
        ),
    ),

    MissingInfoRule(
        category_id="LANDLORD_TERMINATION",
        category_name="Landlord Termination Rights",
        strong_patterns=[
            "landlord may terminate",
            "landlord can terminate",
            "owner may terminate",
            "owner can terminate",
            "termination by landlord",
            "lessor may terminate",
            "lessor can terminate",
            "landlord reserves the right to terminate",
        ],
        weak_patterns=[
            "landlord",
            "owner",
            "lessor",
        ],
        not_found_explanation=(
            "No landlord termination rights could be clearly identified in this "
            "agreement. Consider clarifying under what conditions the landlord "
            "can terminate the agreement."
        ),
        unclear_explanation=(
            "The landlord or owner is mentioned, but their right to terminate "
            "the agreement is not clearly described."
        ),
    ),

    MissingInfoRule(
        category_id="TENANT_TERMINATION",
        category_name="Tenant Termination Rights",
        strong_patterns=[
            "tenant may terminate",
            "tenant can terminate",
            "tenant may vacate",
            "lessee may terminate",
            "lessee can terminate",
            "tenant shall have the right to terminate",
            "tenant termination",
        ],
        weak_patterns=[
            "tenant",
            "lessee",
            "vacate",
        ],
        not_found_explanation=(
            "No tenant termination rights could be clearly identified in this "
            "agreement. Consider clarifying under what conditions you can end "
            "the tenancy."
        ),
        unclear_explanation=(
            "The tenant is mentioned, but your right to terminate the agreement "
            "is not clearly described."
        ),
    ),

    MissingInfoRule(
        category_id="PENALTIES_AND_LIQUIDATED_DAMAGES",
        category_name="Penalties and Liquidated Damages",
        strong_patterns=[
            "liquidated damages",
            "late payment penalty",
            "breach penalty",
            "compensation for breach",
            "damages shall be",
            "penalty clause",
            "penalty of",
            "liable to pay a penalty",
        ],
        weak_patterns=[
            "penalty",
            "damages",
            "compensation",
            "liable",
            "forfeiture",
        ],
        not_found_explanation=(
            "No penalty or liquidated damages terms could be identified in this "
            "agreement. Consider clarifying what financial consequences apply "
            "for breach or default."
        ),
        unclear_explanation=(
            "Financial penalties appear to be mentioned, but the specific "
            "amounts, triggers, or conditions are not clearly stated."
        ),
    ),

    MissingInfoRule(
        category_id="MAINTENANCE_AND_UTILITY_CHARGES",
        category_name="Maintenance and Utility Charges",
        strong_patterns=[
            "electricity charges",
            "water charges",
            "maintenance charges",
            "society charges",
            "utility charges",
            "internet charges",
            "gas charges",
            "common area maintenance",
            "cam charges",
            "municipal charges",
            "property tax",
            "outgoings shall be paid by",
        ],
        weak_patterns=[
            "charges",
            "utilities",
            "electricity",
            "water",
            "maintenance",
        ],
        not_found_explanation=(
            "No utility or maintenance charge responsibilities could be clearly "
            "identified in this agreement. Consider clarifying which recurring "
            "charges you are responsible for."
        ),
        unclear_explanation=(
            "Charges or utilities are mentioned, but it is not clearly stated "
            "which specific charges you are responsible for paying."
        ),
    ),
]

# Lookup by category_id for O(1) access
MISSING_INFO_RULE_BY_CATEGORY: dict = {r.category_id: r for r in MISSING_INFO_RULES}


def classify_category_presence(
    category_id: str,
    all_clause_texts: List[str],
) -> Tuple[str, Optional[str]]:
    """
    Deterministic classification for one category across all clause texts.

    Returns (status, matched_text_or_None).
    Status is one of: PRESENT, UNCLEAR, NOT_IDENTIFIED.

    Does NOT make legal judgments.
    Does NOT invent requirements.
    """
    rule = MISSING_INFO_RULE_BY_CATEGORY.get(category_id)
    if not rule:
        return NOT_IDENTIFIED, None

    combined_lower = " ".join(all_clause_texts).lower()

    # Check strong patterns first
    for pattern in rule.strong_patterns:
        if pattern in combined_lower:
            return PRESENT, pattern

    # Fall back to weak patterns
    for pattern in rule.weak_patterns:
        if pattern in combined_lower:
            return UNCLEAR, pattern

    return NOT_IDENTIFIED, None
