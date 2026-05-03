from apps.repayments.models import Repayment
from apps.loans.models import LoanApplication
from apps.accounts.models import User
from decimal import Decimal
import random
from datetime import date


def run():
    loans = list(LoanApplication.objects.all())
    users = list(User.objects.all())

    for i in range(15):
        loan = random.choice(loans)

        Repayment.objects.create(
            loan=loan,
            amount=Decimal("100000"),
            principal_portion=Decimal("70000"),
            interest_portion=Decimal("30000"),
            channel="mtn_momo",
            payment_date=date.today(),
            recorded_by=random.choice(users)
        )