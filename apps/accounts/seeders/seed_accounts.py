from apps.accounts.models import Branch, User
from django.contrib.auth import get_user_model
import random

User = get_user_model()

def run():
    # --------------------
    # Branches (15)
    # --------------------
    branches = []
    for i in range(15):
        branch, _ = Branch.objects.get_or_create(
            code=f"BR{i+1:03}",
            defaults={
                "name": f"Branch {i+1}",
                "district": "Kampala",
                "phone": f"+256700000{i:02}"
            }
        )
        branches.append(branch)

    # --------------------
    # Users (15)
    # --------------------
    roles = [r[0] for r in User.ROLE_CHOICES]

    for i in range(15):
        username = f"user{i+1}"

        if not User.objects.filter(username=username).exists():
            User.objects.create_user(
                username=username,
                password="Password@123",
                role=random.choice(roles),
                branch=random.choice(branches),
                first_name=f"User{i+1}",
                last_name="Test",
                phone=f"+256701000{i:02}"
            )