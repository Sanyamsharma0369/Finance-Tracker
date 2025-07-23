# Finance Tracker

A Django-based personal finance tracker for managing budgets, transactions, and financial goals.

## Features
- User registration and authentication
- Budget management
- Transaction tracking
- Category and goal management
- Admin dashboard
- Email notifications (password reset, verification)
- Mobile-friendly access

## Getting Started

### Prerequisites
- Python 3.10+
- pip
- (Optional) virtualenv

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Sanyamsharma0369/Finance-Tracker.git
   cd Finance-Tracker
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```sh
   python manage.py migrate
   ```
4. Create a superuser (admin):
   ```sh
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```sh
   python manage.py runserver
   ```

## Usage
- Access the app at `http://127.0.0.1:8000/`
- Log in or register a new account
- Use the dashboard to manage your finances

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License. 