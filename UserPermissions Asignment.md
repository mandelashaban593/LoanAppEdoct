✅ 2. Role → Permission Mapping Table (Implementation Ready)
🔹 Field Officer
Permission
customers | customer | Can add customer
customers | customer | Can view customer
customers | customer document | Can add customer document
customers | customer document | Can view customer document
loans | loan application | Can add loan application (you may need to create this if missing)
loans | loan application | Can view loan application
repayments | repayment | Can add repayment
repayments | repayment | Can view repayment
🔹 Loan Officer
Permission
loans | loan application | Can change loan application
loans | loan application | Can view loan application
loans | approval action | Can add approval action
loans | approval action | Can view approval action
repayments | repayment | Can add repayment
repayments | repayment | Can view repayment
customers | customer | Can view customer
🔹 Branch Manager
Permission
loans | loan application | Can change loan application
loans | loan application | Can view loan application
loans | approval action | Can add approval action
loans | approval action | Can change approval action
loans | approval action | Can view approval action
repayments | repayment | Can add repayment
repayments | repayment | Can change repayment
repayments | repayment | Can view repayment
repayments | penalty waiver | Can add penalty waiver
repayments | penalty waiver | Can view penalty waiver
customers | customer | Can view customer
🔹 Finance Officer
Permission
repayments | repayment | Can add repayment
repayments | repayment | Can change repayment
repayments | repayment | Can view repayment
loans | loan application | Can view loan application
customers | customer | Can view customer
🔹 Managing Director (MD)
Permission
loans | loan application | Can view loan application
loans | approval action | Can add approval action
loans | approval action | Can change approval action
loans | approval action | Can view approval action
repayments | repayment | Can add repayment
repayments | repayment | Can change repayment
repayments | repayment | Can view repayment
repayments | penalty waiver | Can add penalty waiver
repayments | penalty waiver | Can change penalty waiver
repayments | loan restructure | Can add loan restructure
repayments | loan restructure | Can change loan restructure
repayments | loan restructure | Can view loan restructure
customers | customer | Can change customer
customers | customer | Can view customer
🔹 Admin

👉 Full system control

Permission
ALL permissions (including delete, auth, admin, audit logs, users, groups, etc.)
🔹 Auditor
Permission
audit | audit log | Can view audit log
loans | loan application | Can view loan application
repayments | repayment | Can view repayment
customers | customer | Can view customer
customers | collateral | Can view collateral
customers | guarantor | Can view guarantor