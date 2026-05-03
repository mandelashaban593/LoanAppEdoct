from apps.loans.models import LoanProduct, LoanApplication
from apps.accounts.models import User, Branch
from apps.customers.models import Customer
from decimal import Decimal
import random


def run():
    users = list(User.objects.all())
    branches = list(Branch.objects.all())
    customers = list(Customer.objects.all())

    # --------------------
    # Loan Products (15)
    # --------------------
    products = []
    for i in range(15):
        product, _ = LoanProduct.objects.get_or_create(
            code=f"LP{i+1:03}",
            defaults={
                "name": f"Loan Product {i+1}",
                "min_amount": Decimal("100000"),
                "max_amount": Decimal("5000000"),
                "interest_rate": Decimal("5"),
                "created_by": random.choice(users),
            }
        )
        products.append(product)

    # --------------------
    # Loan Applications (15)
    # --------------------
    for i in range(15):
        LoanApplication.objects.create(
            customer=random.choice(customers),
            product=random.choice(products),
            branch=random.choice(branches),
            purpose="business",
            requested_amount=Decimal("1000000"),
            requested_period_months=6,
            created_by=random.choice(users),
        )