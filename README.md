# Finance Tracker

A Django-based Personal Finance Management System designed to help users efficiently manage their budgets, transactions, and financial goals in one place.

## Features
-🔐 User Authentication – Registration, login, and secure access
-💸 Budget Management – Set and monitor budgets for different categories
-📊 Transaction Tracking – Record income and expenses easily
-🎯 Goal Management – Define financial goals and track progress
-🧑‍💼 Admin Dashboard – Manage users, categories, and transactions
-📧 Email Notifications – Password reset and account verification
-📱 Responsive Design – Works smoothly on mobile and desktop

## Getting Started

### Prerequisites
- Python 3.10+
- pip
- (Optional) virtualenv

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Sanyamsharma0369/Finance-Tracker.git
   cd Finance-Tracker
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser (admin):
   ```bash
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage
- Access the app at `http://127.0.0.1:8000/`
- Register or log in to your account
- Use the dashboard to:
         💠Add and view transactions
         💠Manage categories and budgets
         💠Set and monitor financial goals
  
## Tech Stack
- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Database:** SQLite (default) or MySQL
- **Authentication:** Django Auth System
- **Email Services:** Django Email Backend (SMTP)

##Future Enhancements
- 📊 Add expense analytics and charts using Chart.js
- 💾 Support for exporting reports (CSV, PDF)
- 📱 Mobile app version using React Native
- 🔔 Smart alerts for overspending
- 🌐 Multi-user family finance tracking

##Testing
Run all tests using:
```bash
python manage.py test
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License. 
