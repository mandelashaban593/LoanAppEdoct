from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Seed entire system (all apps)"

    def handle(self, *args, **kwargs):
        from apps.accounts.seeders.seed_accounts import run as seed_accounts
        from apps.customers.seeders.seed_customers import run as seed_customers
        from apps.loans.seeders.seed_loans import run as seed_loans
        from apps.repayments.seeders.seed_repayments import run as seed_repayments

        self.stdout.write("🔹 Seeding Accounts...")
        seed_accounts()

        self.stdout.write("🔹 Seeding Customers...")
        seed_customers()

        self.stdout.write("🔹 Seeding Loans...")
        seed_loans()

        self.stdout.write("🔹 Seeding Repayments...")
        seed_repayments()

        self.stdout.write(self.style.SUCCESS("✅ ALL DATA SEEDED SUCCESSFULLY"))