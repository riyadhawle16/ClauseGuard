"""
ClauseGuard Attention Rules — single source of truth.

These are the ONLY predefined categories used for attention analysis.
Do NOT add new categories here without explicit product instruction.
Do NOT derive legal conclusions from these categories.
A match means "worth reviewing", NOT "legally risky".

Each AttentionCategory contains:
  - id:          machine-readable identifier
  - name:        human-readable display name
  - description: explains what the category covers (plain language, no legal advice)
  - patterns:    list of lowercase substrings for deterministic case-insensitive matching
  - explanation_template: plain-language explanation shown to the renter

The deterministic layer scans every extracted clause for pattern matches.
The LLM layer (optional) may confirm or refine the match but cannot invent categories.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AttentionCategory:
    id: str
    name: str
    description: str
    patterns: List[str]
    explanation_template: str


# ── 10 predefined categories ──────────────────────────────────────────────────
# Order does not imply priority or legal significance.

ATTENTION_CATEGORIES: List[AttentionCategory] = [

    AttentionCategory(
        id="SECURITY_DEPOSIT",
        name="Security Deposit",
        description=(
            "Clauses covering security deposit amount, refund conditions, "
            "or deduction terms."
        ),
        patterns=[
            "security deposit",
            "refundable deposit",
            "deposit refund",
            "deposit deduction",
            "deductions from deposit",
            "caution deposit",
            "advance deposit",
            "deposit amount",
        ],
        explanation_template=(
            "This clause contains security deposit terms. "
            "Review the conditions for deductions and when the deposit is returned."
        ),
    ),

    AttentionCategory(
        id="NOTICE_PERIOD",
        name="Notice Period",
        description=(
            "Clauses defining how much notice either party must give "
            "before terminating or vacating."
        ),
        patterns=[
            "notice period",
            "days notice",
            "days' notice",
            "days of notice",
            "written notice",
            "termination notice",
            "advance notice",
            "month's notice",
            "months notice",
            "give notice",
        ],
        explanation_template=(
            "This clause specifies a notice period. "
            "Review how much notice is required and whether the requirement "
            "applies equally to both parties."
        ),
    ),

    AttentionCategory(
        id="LOCK_IN_PERIOD",
        name="Lock-in Period",
        description=(
            "Clauses establishing a minimum tenancy period or restricting "
            "early exit before a specified date."
        ),
        patterns=[
            "lock-in period",
            "lock in period",
            "lockin period",
            "minimum stay",
            "minimum period",
            "minimum tenure",
            "cannot terminate before",
            "early termination during lock",
            "lock-in penalty",
            "lock in penalty",
        ],
        explanation_template=(
            "This clause establishes a lock-in or minimum stay period. "
            "Review the terms for what happens if you need to leave before this period ends."
        ),
    ),

    AttentionCategory(
        id="EARLY_TERMINATION",
        name="Early Termination",
        description=(
            "Clauses describing consequences or conditions of terminating "
            "the agreement before its scheduled end."
        ),
        patterns=[
            "early termination",
            "premature termination",
            "termination before expiry",
            "penalty for leaving early",
            "compensation for early termination",
            "terminate early",
            "vacate before",
            "exit before",
            "forfeit",
        ],
        explanation_template=(
            "This clause describes what happens if the agreement is ended early. "
            "Review any financial consequences or conditions that apply."
        ),
    ),

    AttentionCategory(
        id="MAINTENANCE_RESPONSIBILITY",
        name="Maintenance Responsibility",
        description=(
            "Clauses assigning maintenance, repair, or upkeep responsibility "
            "to the tenant."
        ),
        patterns=[
            "tenant responsible for repairs",
            "tenant shall maintain",
            "tenant must maintain",
            "tenant is responsible",
            "repair costs",
            "appliance repair",
            "plumbing",
            "electrical maintenance",
            "structural repair",
            "minor repairs",
            "major repairs",
            "wear and tear",
            "at tenant's cost",
            "at the tenant's expense",
        ],
        explanation_template=(
            "This clause assigns maintenance or repair responsibility. "
            "Review what you are expected to repair or maintain at your own cost."
        ),
    ),

    AttentionCategory(
        id="RENT_INCREASE",
        name="Rent Increase",
        description=(
            "Clauses describing rent increases, escalation schedules, "
            "or rent revision terms."
        ),
        patterns=[
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
        explanation_template=(
            "This clause describes how the rent may increase. "
            "Review the frequency, amount, and conditions of any rent revision."
        ),
    ),

    AttentionCategory(
        id="LANDLORD_TERMINATION",
        name="Landlord Termination Rights",
        description=(
            "Clauses giving the landlord or owner the right to terminate "
            "the agreement."
        ),
        patterns=[
            "landlord may terminate",
            "landlord can terminate",
            "owner may terminate",
            "owner can terminate",
            "termination by landlord",
            "landlord reserves the right to terminate",
            "lessor may terminate",
            "lessor can terminate",
            "owner terminate",
        ],
        explanation_template=(
            "This clause describes the landlord's right to terminate the agreement. "
            "Review the conditions and notice requirements that apply."
        ),
    ),

    AttentionCategory(
        id="TENANT_TERMINATION",
        name="Tenant Termination Rights",
        description=(
            "Clauses describing the tenant's right or ability to terminate "
            "the agreement."
        ),
        patterns=[
            "tenant may terminate",
            "tenant can terminate",
            "tenant may vacate",
            "tenant shall have the right to terminate",
            "lessee may terminate",
            "lessee can terminate",
            "tenant termination",
        ],
        explanation_template=(
            "This clause describes your right to terminate the agreement. "
            "Review the conditions and notice requirements that apply to you."
        ),
    ),

    AttentionCategory(
        id="PENALTIES_AND_LIQUIDATED_DAMAGES",
        name="Penalties and Liquidated Damages",
        description=(
            "Clauses specifying monetary penalties, compensation obligations, "
            "or liquidated damages."
        ),
        patterns=[
            "penalty",
            "liquidated damages",
            "late payment penalty",
            "breach penalty",
            "compensation for breach",
            "damages shall be",
            "liable to pay",
            "forfeiture",
            "penal",
        ],
        explanation_template=(
            "This clause specifies penalties or financial consequences. "
            "Review the conditions that trigger these obligations and the amounts involved."
        ),
    ),

    AttentionCategory(
        id="MAINTENANCE_AND_UTILITY_CHARGES",
        name="Maintenance and Utility Charges",
        description=(
            "Clauses assigning recurring utility or maintenance charge "
            "responsibility to the tenant."
        ),
        patterns=[
            "electricity charges",
            "water charges",
            "maintenance charges",
            "society charges",
            "utility charges",
            "internet charges",
            "gas charges",
            "common area maintenance",
            "cam charges",
            "outgoings",
            "municipal charges",
            "property tax",
        ],
        explanation_template=(
            "This clause assigns utility or maintenance charges. "
            "Review which recurring charges you are responsible for paying."
        ),
    ),
]

# Build a lookup dict for O(1) access by category id
CATEGORY_BY_ID: dict = {cat.id: cat for cat in ATTENTION_CATEGORIES}
VALID_CATEGORY_IDS: set = {cat.id for cat in ATTENTION_CATEGORIES}


def match_clause_to_categories(clause_text: str) -> List[tuple]:
    """
    Deterministic layer: scan clause_text against all predefined patterns.

    Returns a list of (AttentionCategory, matched_pattern) tuples for every
    category whose patterns appear in the normalised clause text.

    Case-insensitive. Does NOT use the LLM.
    Does NOT generate legal conclusions.
    """
    normalised = clause_text.lower()
    results = []
    for category in ATTENTION_CATEGORIES:
        for pattern in category.patterns:
            if pattern in normalised:
                results.append((category, pattern))
                break   # one match per category is enough for deterministic detection
    return results
