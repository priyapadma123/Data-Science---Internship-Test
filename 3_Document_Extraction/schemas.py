"""Defines, for each of the 10 target document types, which fields to
extract, and a regex validator for fields that have a checkable format.
Fields with no validator (names, places, free text) rely purely on the
model's own confidence score.
"""

CONFIDENCE_THRESHOLD = 0.75
# Rationale: this is insurance onboarding data (bank details, identity numbers).
# A wrong IFSC/account number silently accepted can mis-route real money, and
# a wrong identity number can cause compliance issues. The cost of a false
# negative (flagging something that was actually fine) is a few minutes of
# human review. The cost of a false positive (auto-accepting a wrong value)
# is a financial/compliance error. We deliberately bias toward over-flagging
# (recall over precision) - so the threshold is set fairly high at 0.75.

DOCUMENT_TYPES = {
    "aadhaar_card": {
        "label": "Aadhaar Card",
        "fields": {
            "aadhaar_number": r"^\d{4}\s?\d{4}\s?\d{4}$",
            "full_name": None,
            "date_of_birth": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "address": None,
        },
    },
    "pan_card": {
        "label": "PAN Card",
        "fields": {
            "pan_number": r"^[A-Z]{5}[0-9]{4}[A-Z]$",
            "full_name": None,
            "fathers_name": None,
            "date_of_birth": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
        },
    },
    "driving_licence": {
        "label": "Driving Licence",
        "fields": {
            "dl_number": r"^[A-Z]{2}[\dA-Z\s]{8,15}$",
            "name": None,
            "date_of_issue": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "valid_till": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
        },
    },
    "passport": {
        "label": "Passport",
        "fields": {
            "passport_number": r"^[A-Z][0-9]{7}$",
            "date_of_birth": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "date_of_expiry": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "mrz_line_2": r"^[A-Z0-9<]{40,44}$",
        },
    },
    "nach_ecs_mandate": {
        "label": "NACH / ECS Mandate",
        "fields": {
            "bank_account_number": r"^\d{6,18}$",
            "ifsc_code": r"^[A-Z]{4}0[A-Z0-9]{6}$",
            "bank_name": None,
            "amount_figures": r"^[\d,]+(\.\d{1,2})?$",
            "frequency": None,
        },
    },
    "fatca_annexure": {
        "label": "FATCA Annexure Form",
        "fields": {
            "policy_number": r"^\d{6,15}$",
            "tin_pan": r"^[A-Z0-9]{8,12}$",
            "fathers_name": None,
            "place_of_birth": None,
            "nationality": None,
        },
    },
    "benefit_illustration_declaration": {
        "label": "Benefit Illustration Declaration",
        "fields": {
            "application_number": r"^\d{6,15}$",
            "policyholder_name": None,
            "date": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "place": None,
        },
    },
    "moral_hazard_questionnaire": {
        "label": "Moral Hazard Questionnaire",
        "fields": {
            "application_number": r"^\d{6,15}$",
            "name_of_life_assured": None,
            "nominee_relationship": None,
            "date": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "place": None,
        },
    },
    "multiple_policies_consent": {
        "label": "Multiple Policies Consent Form",
        "fields": {
            "proposer_name": None,
            "reason_for_multiple_policies": None,
            "date": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "place": None,
        },
    },
    "suitability_profiler_declaration": {
        "label": "Suitability Profiler Declaration",
        "fields": {
            "application_number": r"^\d{6,15}$",
            "name_of_life_assured": None,
            "name_of_agent_sp": None,
            "date": r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$",
            "place": None,
        },
    },
}

# Which of these are inherently handwritten documents (affects how we frame
# the extraction prompt and how we explain failures in the README).
HANDWRITTEN_TYPES = {
    "nach_ecs_mandate",
    "fatca_annexure",
    "benefit_illustration_declaration",
    "moral_hazard_questionnaire",
    "multiple_policies_consent",
    "suitability_profiler_declaration",
}
