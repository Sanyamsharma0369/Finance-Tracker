# Finance Tracker - Project Explanation

## Overview
Finance Tracker is a comprehensive web application designed to help users manage their personal and commercial finances. The platform provides tools for tracking income, expenses, budgets, financial goals, and generating insightful reports. It supports both individual and admin (staff) users, with advanced features for data analysis, system diagnostics, and user management.

---

## Main Features & Functionalities
- **User Authentication:** Secure login, registration, and profile management for users and admins.
- **Transaction Management:** Add, edit, delete, and categorize income and expense transactions. Supports recurring transactions and receipt uploads.
- **Budgeting:** Create and monitor budgets for different categories and time periods (daily, weekly, monthly, yearly).
- **Financial Goals:** Set, track, and update progress towards savings or spending goals, with deadlines and progress bars.
- **Reporting & Analytics:** Visual dashboards, charts (using Chart.js), and downloadable reports (PDF export) for financial analysis.
- **Notifications:** In-app and email notifications for reminders, alerts, and system messages.
- **Admin Panel:** Advanced dashboard for system monitoring, user management, transaction oversight, and system diagnostics.
- **Settings:** User-customizable settings for currency (default: INR ₹), theme (light/dark), notifications, and localization.
- **Security:** Role-based access, data validation, and system health monitoring.

---

## Technologies & Languages Used
- **Backend:** Python 3, Django 5.2 (MVC web framework)
- **Frontend:** HTML5, CSS3 (Bootstrap 5), JavaScript (ES6+), Chart.js
- **Database:** SQLite (default, can be swapped for PostgreSQL/MySQL)
- **Other:** Django ORM, Django Admin, jQuery (for DataTables), ReportLab (PDF generation)

---

## Contribution Breakdown (Easy to Hard)
1. **Member 1:** Frontend UI/UX (HTML, CSS, Bootstrap) - Easy
2. **Member 2:** Basic CRUD Operations (Django Views, Templates) - Easy to Moderate
3. **Member 3:** Data Visualization & Charts (JavaScript, Chart.js) - Moderate
4. **Member 4:** Backend Logic & API Integration (Python, Django) - Moderate to Hard
5. **Member 5:** Advanced Features & Security (Authentication, PDF Export, System Diagnostics) - Hard

---

## Languages Used
- **Python:** Backend logic, Django framework
- **HTML:** Structure of web pages
- **CSS:** Styling and layout
- **JavaScript:** Frontend interactivity, Chart.js for data visualization
- **SQL:** Database queries (via Django ORM)

---

## Database Schema (Core Models)

### User (Django's built-in)
- `username`, `email`, `password`, `is_staff`, `is_active`, etc.

### UserProfile
- `user` (OneToOne to User)
- `phone_number`, `profile_picture`, `is_commercial`, `created_at`, `updated_at`

### Category
- `id`, `name`, `type` (income/expense), `description`, `user` (ForeignKey), `created_at`, `updated_at`

### Transaction
- `id`, `user` (ForeignKey), `amount`, `category` (ForeignKey), `description`, `date`, `type` (income/expense), `receipt`, `is_recurring`, `recurring_frequency`, `created_at`, `updated_at`

### Budget
- `id`, `category` (ForeignKey), `amount`, `period` (daily/weekly/monthly/yearly), `user` (ForeignKey), `created_at`, `updated_at`

### FinancialGoal
- `id`, `user` (ForeignKey), `name`, `target_amount`, `current_amount`, `deadline`, `category` (ForeignKey, nullable), `created_at`, `updated_at`
- **Property:** `progress` (percentage of current_amount/target_amount)

### Notification
- `id`, `user` (ForeignKey), `message`, `created_at`, `is_read`

### Settings
- `id`, `user` (OneToOne), `currency` (choices: USD, EUR, GBP, JPY, INR), `theme` (light/dark/system), `notifications_enabled`, `email_notifications`, `budget_alerts`, `goal_reminders`, `language`, `timezone`, `date_format`, `created_at`, `updated_at`

---

## Migration History (Key Points)
- Initial models: Category, Budget, FinancialGoal, Notification, Transaction
- Added fields: `category` to FinancialGoal, `created_at`/`updated_at` to most models
- Settings model: for user preferences (currency, theme, etc.)
- OTP model: for email verification and security
- Choices for currency and theme updated to support INR (₹) as default

---

## Project Structure
- `core/` - Main Django app (models, views, templates, migrations)
- `templates/` - Global and admin HTML templates
- `static/` - CSS, JS, images
- `media/` - User-uploaded files (receipts, profile pictures)
- `db.sqlite3` - Default database

---

## How It Works
1. **Users** register and log in to manage their finances.
2. **Transactions** are added with categories, amounts, and optional receipts.
3. **Budgets** and **goals** help users plan and track their financial targets.
4. **Admins** can view all users, transactions, and system health from the admin dashboard.
5. **Reports** and **charts** provide insights into spending, income, and progress.
6. **Settings** allow users to customize their experience (currency, theme, notifications).

---

## Notable Functionalities
- Dynamic currency support (default: INR ₹)
- Responsive, modern UI with Bootstrap and Chart.js
- DataTables for advanced table filtering and sorting
- PDF export for reports
- Modular, extensible Django codebase

---

## Authors & Credits
- Developed by the Finance Tracker Team
- Built with Django, Bootstrap, and open-source libraries

---

## For Developers
- Clone the repo, install requirements, and run migrations
- Start the server with `python manage.py runserver`
- Default admin panel at `/admin/` (Django admin) and `/manage/` (custom admin dashboard)

---

## License
This project is for educational and demonstration purposes only. 