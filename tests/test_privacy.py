import unittest

import pandas as pd

from core.privacy import (
    apply_column_overrides,
    detect_sensitive_columns,
    mask_sensitive_data,
    mask_sensitive_text,
)


class PrivacyProtectionTest(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "Customer_ID": [101, 102, 101],
                "Email": ["a@example.com", "b@example.com", "a@example.com"],
                "Phone": ["+27 82 123 4567", "+27 82 987 6543", None],
                "Annual Income": [500000, 750000, 500000],
                "Product Name": ["Laptop", "Monitor", "Laptop"],
                "Revenue": [1200.0, 850.0, 1200.0],
            }
        )

    def test_detects_pii_and_psi_without_masking_business_columns(self):
        findings = detect_sensitive_columns(self.df)

        self.assertEqual(findings["Customer_ID"]["category"], "PII")
        self.assertEqual(findings["Email"]["category"], "PII")
        self.assertEqual(findings["Phone"]["category"], "PII")
        self.assertEqual(findings["Annual Income"]["category"], "PSI")
        self.assertNotIn("Product Name", findings)
        self.assertNotIn("Revenue", findings)

    def test_detects_camel_case_and_run_together_column_names(self):
        df = pd.DataFrame(
            {
                "EmailAddress": ["a@example.com"],
                "FirstName": ["Ann"],
                "customerName": ["Ann Lee"],
                "Surname": ["Lee"],
                "sur_name": ["Lee"],
                "Condition": ["asthma"],
            }
        )
        findings = detect_sensitive_columns(df)

        self.assertEqual(set(findings), set(df.columns))

    def test_does_not_flag_business_columns_that_look_sensitive(self):
        df = pd.DataFrame(
            {
                "item_condition": ["new"],
                "product_name": ["Laptop"],
                "company_name": ["Acme"],
                "OrderTotal": [10.0],
            }
        )

        self.assertEqual(detect_sensitive_columns(df), {})

    def test_column_overrides_add_and_release_columns(self):
        findings = detect_sensitive_columns(self.df)
        adjusted = apply_column_overrides(
            findings, protect=["Product Name"], keep=["Annual Income"]
        )

        self.assertEqual(adjusted["Product Name"]["reason"], "user selection")
        self.assertNotIn("Annual Income", adjusted)
        self.assertIn("Email", adjusted)
        self.assertNotIn("Product Name", findings)

    def test_masking_is_consistent_and_preserves_non_sensitive_values(self):
        findings = detect_sensitive_columns(self.df)
        protected = mask_sensitive_data(self.df, findings, "test-salt")

        self.assertNotEqual(protected.loc[0, "Email"], self.df.loc[0, "Email"])
        self.assertEqual(protected.loc[0, "Email"], protected.loc[2, "Email"])
        self.assertTrue(pd.isna(protected.loc[2, "Phone"]))
        self.assertEqual(protected["Product Name"].tolist(), self.df["Product Name"].tolist())
        self.assertEqual(protected["Revenue"].tolist(), self.df["Revenue"].tolist())

    def test_masks_sensitive_values_in_chat_text(self):
        protected = mask_sensitive_text(
            "Contact me at analyst@example.com or +27 82 123 4567.",
            "test-salt",
        )

        self.assertNotIn("analyst@example.com", protected)
        self.assertNotIn("82 123 4567", protected)
        self.assertIn("<MASKED-EMAIL>", protected)
        self.assertIn("<MASKED-PHONE>", protected)


if __name__ == "__main__":
    unittest.main()
