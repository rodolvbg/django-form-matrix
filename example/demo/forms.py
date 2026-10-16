from django import forms

from django_form_matrix import Column, MatrixField, Row

FEATURES = [
    Row("invoices", "Invoices", section="Billing"),
    Row("quotes", "Quotes", section="Billing"),
    Row("reports", "Reports", section="Analytics"),
    Row("exports", "Exports", section="Analytics", columns=["enabled"]),
]


class PlanForm(forms.ModelForm):
    features = MatrixField(
        rows=FEATURES,
        columns=[
            Column("enabled", "Enabled"),
            Column(
                "limit",
                "Monthly limit",
                forms.IntegerField(min_value=0, required=False),
            ),
            Column(
                "support",
                "Support",
                forms.ChoiceField(
                    choices=[("", "—"), ("email", "Email"), ("phone", "Phone")],
                    required=False,
                ),
            ),
        ],
    )

    class Meta:
        fields = ["name", "features"]
