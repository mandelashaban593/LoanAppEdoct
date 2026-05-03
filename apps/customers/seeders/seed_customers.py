from apps.customers.models import Customer, Guarantor, Collateral
from apps.accounts.models import User, Branch
import random
from decimal import Decimal


def run():
    users = list(User.objects.all())
    branches = list(Branch.objects.all())

    for i in range(15):
        nin = f"CF0000000000{i:02}"

        customer, created = Customer.objects.get_or_create(
            nin=nin,
            defaults={
                "full_name": f"Customer {i+1}",
                "primary_phone": f"+256772000{i:02}",
                "district": "Kampala",
                "village_lc1": "Ntinda",
                "physical_address": "Kampala Uganda",
                "next_of_kin_name": "Relative",
                "next_of_kin_phone": "+256701111111",
                "customer_type": "business",
                "employer_business": "Retail",
                "occupation": "Trader",
                "monthly_income": Decimal("500000"),
                "monthly_expenses": Decimal("200000"),
                "branch": random.choice(branches),
                "created_by": random.choice(users),
            }
        )

        if created:
            # Guarantor
            Guarantor.objects.create(
                customer=customer,
                full_name=f"Guarantor {i+1}",
                nin=f"GUAR{i}",
                phone="+256700111111",
                relationship="Friend"
            )

            # Collateral
            Collateral.objects.create(
                customer=customer,
                collateral_type="vehicle",
                description="Car",
                market_value=Decimal("2000000"),
                forced_sale_value=Decimal("1500000"),
                verified_by=random.choice(users)
            )