"""
Management command: python manage.py seed_data

Seeds the database with demo merchants, bank accounts,
and initial credit ledger entries to enable payout testing.
"""

from django.core.management.base import BaseCommand
from apps.merchants.models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry


SEED_MERCHANTS = [
    {
        "name": "Acme Corp",
        "email": "finance@acme.com",
        "bank": {"account_number": "9876543210", "ifsc_code": "HDFC0001234", "account_holder_name": "Acme Corp Ltd"},
        "credit_paise": 500_000_00,  # ₹5,00,000
    },
    {
        "name": "Beacon Retail",
        "email": "payments@beacon.com",
        "bank": {"account_number": "1234567890", "ifsc_code": "ICIC0005678", "account_holder_name": "Beacon Retail Pvt Ltd"},
        "credit_paise": 200_000_00,  # ₹2,00,000
    },
    {
        "name": "Nexus Ventures",
        "email": "ops@nexus.io",
        "bank": {"account_number": "5555666677", "ifsc_code": "SBIN0009876", "account_holder_name": "Nexus Ventures Inc"},
        "credit_paise": 100_000_00,  # ₹1,00,000
    },
]


class Command(BaseCommand):
    help = "Seed database with demo merchants and initial credit balances"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding LedgerX demo data...")

        for data in SEED_MERCHANTS:
            merchant, created = Merchant.objects.get_or_create(
                email=data["email"],
                defaults={"name": data["name"]},
            )

            bank_account, _ = BankAccount.objects.get_or_create(
                merchant=merchant,
                account_number=data["bank"]["account_number"],
                defaults={
                    "ifsc_code": data["bank"]["ifsc_code"],
                    "account_holder_name": data["bank"]["account_holder_name"],
                },
            )

            # Only add initial credit if merchant is newly created
            if created:
                LedgerEntry.objects.create(
                    merchant=merchant,
                    type=LedgerEntry.EntryType.CREDIT,
                    amount_paise=data["credit_paise"],
                    reference_type=LedgerEntry.ReferenceType.CREDIT,
                    description="Initial credit from platform",
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Created {merchant.name} with ₹{data['credit_paise'] / 100:,.2f} balance"
                    )
                )
            else:
                self.stdout.write(
                    f"  — {merchant.name} already exists, skipping."
                )

        self.stdout.write(self.style.SUCCESS("\n✅ Seed complete!"))
