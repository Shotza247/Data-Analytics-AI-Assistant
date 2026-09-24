import hashlib
import hmac
import math
import re
import secrets

import pandas as pd


PII_COLUMN_PATTERNS = (
    r"^(?:name|full_name|first_name|last_name|surname|contact_name)$",
    r"(?:^|_)(?:email|e_mail|phone|telephone|mobile|fax)(?:_|$)",
    r"(?:^|_)(?:address|street_address|home_address|postal_code|zip_code)(?:_|$)",
    r"(?:^|_)(?:ssn|social_security|national_id|passport|driver_license|drivers_license)(?:_|$)",
    r"(?:^|_)(?:ip_address|mac_address|username|user_name)(?:_|$)",
    r"^(?:customer|client|user|employee|patient|member|account|transaction)_?id$",
    r"^id$",
)

PSI_COLUMN_PATTERNS = (
    r"(?:^|_)(?:dob|date_of_birth|birth_date)(?:_|$)",
    r"(?:^|_)(?:gender|sex|race|ethnicity|religion|disability)(?:_|$)",
    r"(?:^|_)(?:medical|diagnosis|condition|health|biometric|insurance)(?:_|$)",
    r"(?:^|_)(?:salary|income|bank_account|account_number|iban|swift)(?:_|$)",
    r"(?:^|_)(?:credit_card|card_number|credit_score|credit_history|tax_id)(?:_|$)",
    r"(?:^|_)(?:password|passcode|pin|cvv|api_key|secret|access_token)(?:_|$)",
)

VALUE_PATTERNS = {
    "PII": (
        re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$"),
        re.compile(r"^\d{3}-\d{2}-\d{4}$"),
        re.compile(r"^(?:\+?\d[\d\s().-]{6,}\d)$"),
        re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$"),
    ),
    "PSI": (
        re.compile(r"^(?:\d[ -]*?){13,19}$"),
    ),
}

TEXT_REDACTIONS = (
    (re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b"), "<MASKED-EMAIL>"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "<MASKED-SSN>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<MASKED-IP>"),
    (re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)"), "<MASKED-PHONE>"),
)


def create_masking_salt():
    return secrets.token_hex(16)


def normalize_column_name(column):
    return re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")


def _column_category(column):
    normalized = normalize_column_name(column)
    for pattern in PII_COLUMN_PATTERNS:
        if re.search(pattern, normalized):
            return "PII", "column name"
    for pattern in PSI_COLUMN_PATTERNS:
        if re.search(pattern, normalized):
            return "PSI", "column name"
    return None


def _value_category(series):
    if pd.api.types.is_numeric_dtype(series):
        return None

    sample = series.dropna().astype(str).str.strip().head(100)
    if sample.empty:
        return None

    minimum_matches = max(1, math.ceil(len(sample) * 0.6))
    for category, patterns in VALUE_PATTERNS.items():
        for pattern in patterns:
            if sample.str.fullmatch(pattern).sum() >= minimum_matches:
                return category, "value pattern"
    return None


def detect_sensitive_columns(df):
    findings = {}
    for column in df.columns:
        finding = _column_category(column) or _value_category(df[column])
        if finding:
            category, reason = finding
            findings[str(column)] = {"category": category, "reason": reason}
    return findings


def _masked_value(value, category, salt):
    if pd.isna(value):
        return value
    digest = hmac.new(
        salt.encode("utf-8"),
        f"{category}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:10].upper()
    return f"<{category}-{digest}>"


def mask_sensitive_data(df, findings, salt):
    protected = df.copy(deep=True)
    for column, details in findings.items():
        if column in protected.columns:
            protected[column] = protected[column].map(
                lambda value: _masked_value(value, details["category"], salt)
            )
    return protected


def mask_sensitive_text(text, salt):
    protected = text or ""
    for pattern, replacement in TEXT_REDACTIONS:
        protected = pattern.sub(replacement, protected)
    return protected
