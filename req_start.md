# Finance Tracker - Setup and Running Guide

This guide will help you set up and run the Finance Tracker application on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:
- Python (version 3.8 or higher)
- pip (Python package installer)
- Git (optional, for version control)

## Step 1: Clone the Repository (if using Git)
```bash
git clone [your-repository-url]
cd finance_tracker
```

## Step 2: Set Up a Virtual Environment
It's recommended to use a virtual environment to manage dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies
The project uses several Python packages. Install them using pip:

```bash
pip install -r requirements.txt
```

This will install the following dependencies:
- Django==5.2
- Pillow==10.2.0
- django-crispy-forms==2.1
- crispy-bootstrap5==2024.2

## Step 4: Database Setup
1. Run migrations to set up the database:
```bash
python manage.py migrate
```

2. Create a superuser (admin account):
```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin account.

## Step 5: Run the Development Server
1. Start the development server:
```bash
python manage.py runserver
```

2. Open your web browser and navigate to:
```
http://127.0.0.1:8000/
```

## Additional Information

### Project Structure
- `manage.py`: Django's command-line utility for administrative tasks
- `finance_tracker/`: Main project directory
- `templates/`: Contains HTML templates
- `static/`: Contains static files (CSS, JavaScript, images)
- `media/`: Contains user-uploaded files

### Common Issues and Solutions
1. If you get a "ModuleNotFoundError":
   - Make sure your virtual environment is activated
   - Verify all dependencies are installed correctly

2. If the server won't start:
   - Check if port 8000 is already in use
   - Ensure you're in the correct directory
   - Verify Django is installed correctly

3. If static files aren't loading:
   - Run `python manage.py collectstatic`
   - Check your static files configuration in settings.py

### Stopping the Server
To stop the development server, press `Ctrl+C` in the terminal where the server is running.

## Need Help?
If you encounter any issues or need further assistance, please:
1. Check the Django documentation
2. Review the project's issue tracker
3. Contact the development team

Remember to deactivate your virtual environment when you're done:
```bash
deactivate
``` 