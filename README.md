# Loan Management System (LMS)
## Django Web Application — Uganda Context

---

## Prerequisites

- Python 3.10 or higher
- pip

---

## 1. Set Up Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

source loanenv/Scripts/activate

# macOS / Linux
source venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Apply Database Migrations

```bash
python manage.py makemigrations accounts customers loans repayments notifications audit
python manage.py migrate
```

---

## 4. Seed Demo Data

Creates 4 branches, 7 users (one per role), 3 loan products, and 3 demo customers.

```bash
python manage.py seed_demo
```

**All demo users share the password:** `Demo@1234`

| Username       | Role                  | Branch        |
|----------------|-----------------------|---------------|
| admin          | System Administrator  | Kampala HQ    |
| md             | Managing Director     | Kampala HQ    |
| loan.officer   | Loan Officer          | Kampala HQ    |
| field.officer  | Field Officer         | Kampala HQ    |
| branch.mgr     | Branch Manager        | Wakiso Branch |
| finance        | Finance Officer       | Kampala HQ    |
| auditor        | Internal Auditor (read-only) | Kampala HQ |

---

## 5. Run the Development Server

```bash
python manage.py runserver
```

Open: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)

---

## 6. Media File Storage

Upload directories are created automatically. For production, configure S3 or a
dedicated file server and update `MEDIA_ROOT` / `DEFAULT_FILE_STORAGE` in settings.

```bash
mkdir -p media/customers/{photos,ids,documents} media/guarantors/ids media/collaterals
```

---

## Application Structure

```
loansystem/
├── manage.py
├── requirements.txt
├── loansystem/
│   ├── settings.py       — Project configuration
│   └── urls.py           — Root URL routing
├── apps/
│   ├── accounts/         — Custom User, Branch, login, dashboard, roles
│   ├── customers/        — KYC, employment, guarantors, collateral, documents
│   ├── loans/            — Products, applications, approval workflow, schedule
│   ├── repayments/       — Payment recording, penalty waiver, restructuring
│   ├── notifications/    — In-app alerts for every workflow event
│   ├── reports/          — Portfolio, arrears, defaulters, active loans
│   └── audit/            — Full audit trail for all user actions
└── templates/
    ├── base/base.html    — Sidebar + topbar responsive layout (Bootstrap 5)
    ├── accounts/         — Login, change password
    ├── dashboard/        — KPI dashboard
    ├── customers/        — List, detail, form
    ├── loans/            — List, detail, form, approve, review, disburse
    ├── repayments/       — Record payment, waiver, restructure
    ├── reports/          — Portfolio, arrears, defaulters, active loans
    ├── notifications/    — Notification inbox
    └── audit/            — Audit log viewer
```

---

## Approval Workflow

```
Field Officer → Creates Draft → Submits
       ↓
Loan Officer → Starts Review → Credit Assessment
       ↓
Managing Director → Final Approval (required for loans > UGX 5,000,000)
       ↓
Finance Officer → Disburses → Repayment Schedule Auto-Generated
       ↓
Active Loan → Field Officer Records Repayments → Closed on Full Settlement
```

At any stage, an approver can:
- **Return** for correction (with mandatory reason)
- **Reject** outright (with mandatory reason, logged in audit trail)

---

## Role Permissions Summary

| Action                  | Field Officer | Loan Officer | Branch Manager | Finance Officer | MD  | Admin | Auditor |
|-------------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Create application      | ✓   |     |     |     |     | ✓   |     |
| Submit application      | ✓   |     |     |     |     | ✓   |     |
| Start review            |     | ✓   | ✓   |     |     | ✓   |     |
| Approve (< UGX 5M)      |     | ✓   | ✓   |     | ✓   | ✓   |     |
| Approve (> UGX 5M)      |     |     |     |     | ✓   | ✓   |     |
| Disburse                |     |     |     | ✓   | ✓   | ✓   |     |
| Record repayment        | ✓   | ✓   | ✓   | ✓   | ✓   | ✓   |     |
| Waive penalty           |     |     | ✓   |     | ✓   | ✓   |     |
| Restructure loan        |     |     |     |     | ✓   | ✓   |     |
| Blacklist customer      |     |     |     |     | ✓   | ✓   |     |
| View audit logs         |     |     |     |     |     | ✓   | ✓   |
| Delete records          |     |     |     |     |     | ✓   |     |

---

## Security Features

- Account locks after **5 failed login attempts** (Admin unlocks in Django Admin)
- **Session expires** after 10 minutes of inactivity
- **Forced password change** on first login
- Password policy: minimum 8 characters, must include a number
- All actions written to **AuditLog** (login, create, approve, disburse, waiver, export)
- Approved loan records are **locked** — cannot be edited
- Branch-scoped data: users only see their own branch unless MD/Admin/Auditor
- CSRF protection on all forms

---

## Production Checklist

Before going live:

1. Set `DEBUG = False` in `settings.py`
2. Replace `SECRET_KEY` with a secure environment variable
3. Configure PostgreSQL in `DATABASES`
4. Set `ALLOWED_HOSTS` to your domain
5. Configure real email (Microsoft 365 / Africa's Talking for SMS)
6. Set up `STATIC_ROOT` and run `python manage.py collectstatic`
7. Use Gunicorn + Nginx for serving
8. Enable HTTPS with Let's Encrypt
9. Set up daily database backups

---

## Django Admin

Access at `/admin/` using the `admin` account.

From admin you can:
- Unlock locked user accounts
- Force password resets
- Create and configure loan products
- Set up branches and branch codes
- View and manage all data across the system
- Write off loans in bulk

---

*Built for Uganda microfinance institutions — Kampala, Uganda*
"# Loan-Management-System" 


## Test User

## Admin
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='admin')  # change username
user.set_password('admin123')
user.save()

print("Password reset successfully")

## field_Officer
{
    "id": 25,
    "username": "peter_doe",
    "first_name": "",
    "last_name": "",
    "email": "peter@example.com",
    "role": "field_officer",
    "branch": 1,
    "phone": ""
}


## loan_Officer
{
  "username": "john_doe",
  "password": "StrongPassword123!",
  "email": "john@example.com",
  "role": "loan_officer",
  "branch": 1
}


## branch_manager
{
    "id": 26,
    "username": "patrick_doe",
    "first_name": "",
    "last_name": "",
    "email": "patrick@example.com",
    "role": "branch_manager",
    "branch": 1,
    "phone": ""
}


## managing_director
{
    "id": 27,
    "username": "samuel_doe",
    "first_name": "",
    "last_name": "",
    "password": "StrongPassword234!",
    "email": "samuel@example.com",
    "role": "managing_director",
    "branch": 1,
    "phone": ""
}


## auditor
{
    "id": 28,
    "username": "james_doe",
    "first_name": "",
    "last_name": "",
    "email": "james@example.com",
    "role": "auditor",
    "branch": 1,
    "phone": ""
}# LoanAppEdoct
