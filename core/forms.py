from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import Category, Transaction, Budget, FinancialGoal, Settings, UserProfile, CommercialRegistration, EmailConfig

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        }),
        help_text="Required. Enter a valid email address."
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered. Please use a different email.")
        return email

class CommercialRegistrationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    company_name = forms.CharField(
        label='Company Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your company name'
        })
    )
    business_type = forms.ChoiceField(
        label='Business Type',
        choices=CommercialRegistration.BUSINESS_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    registration_number = forms.CharField(
        label='Business Registration Number',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your business registration number'
        })
    )
    tax_id = forms.CharField(
        label='Tax ID',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your tax ID number'
        })
    )
    business_address = forms.CharField(
        label='Business Address',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your business address',
            'rows': 3
        })
    )
    phone_number = forms.CharField(
        label='Business Phone',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your business phone number'
        })
    )
    business_document = forms.FileField(
        label='Business Documents',
        help_text='Upload a PDF or image of your business registration document',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        email = cleaned_data.get('email')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered')
        
        return cleaned_data

class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    is_staff = forms.BooleanField(
        required=False, 
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_active = forms.BooleanField(
        required=False, 
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = self.cleaned_data['is_staff']
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(user=user)
            
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'description']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'description', 'date', 'type', 'receipt', 'is_recurring', 'recurring_frequency']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'period']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget amount',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'period': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Budget amount must be greater than zero.")
        return amount

class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ['name', 'target_amount', 'current_amount', 'deadline', 'category']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = [
            'currency',
            'theme',
            'notifications_enabled',
            'email_notifications',
            'budget_alerts',
            'goal_reminders',
            'language',
            'timezone',
            'date_format'
        ]
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('en', 'English'),
                ('hi', 'Hindi'),
                ('es', 'Spanish'),
                ('fr', 'French'),
                ('de', 'German')
            ]),
            'timezone': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('UTC', 'UTC'),
                ('Asia/Kolkata', 'India Standard Time'),
                ('US/Eastern', 'US Eastern Time'),
                ('US/Pacific', 'US Pacific Time'),
                ('Europe/London', 'London'),
                ('Europe/Paris', 'Paris')
            ]),
            'date_format': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('%Y-%m-%d', 'YYYY-MM-DD'),
                ('%d-%m-%Y', 'DD-MM-YYYY'),
                ('%m-%d-%Y', 'MM-DD-YYYY'),
                ('%d/%m/%Y', 'DD/MM/YYYY'),
                ('%m/%d/%Y', 'MM/DD/YYYY'),
            ]),
        }

class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP',
            'pattern': '[0-9]{6}',
            'title': 'Please enter a 6-digit number'
        })
    )

class UserSettingsForm(forms.Form):
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    phone_number = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    currency = forms.ChoiceField(
        choices=Settings.CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    theme = forms.ChoiceField(
        choices=Settings.THEME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notifications_enabled = forms.BooleanField(required=False, initial=True)
    email_notifications = forms.BooleanField(required=False, initial=True)
    budget_alerts = forms.BooleanField(required=False, initial=True)
    goal_reminders = forms.BooleanField(required=False, initial=True)
    language = forms.ChoiceField(
        choices=[
            ('en', 'English'),
            ('hi', 'Hindi'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    timezone = forms.ChoiceField(
        choices=[
            ('UTC', 'UTC'),
            ('Asia/Kolkata', 'India Standard Time'),
            ('US/Eastern', 'US Eastern Time'),
            ('US/Pacific', 'US Pacific Time'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_format = forms.ChoiceField(
        choices=[
            ('%Y-%m-%d', 'YYYY-MM-DD'),
            ('%d-%m-%Y', 'DD-MM-YYYY'),
            ('%m-%d-%Y', 'MM-DD-YYYY'),
            ('%d/%m/%Y', 'DD/MM/YYYY'),
            ('%m/%d/%Y', 'MM/DD/YYYY'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class EmailConfigForm(forms.ModelForm):
    email_host_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = EmailConfig
        fields = [
            'email_backend',
            'email_host',
            'email_port',
            'email_use_tls',
            'email_use_ssl',
            'email_host_user',
            'email_host_password',
            'default_from_email',
            'is_active'
        ]
        widgets = {
            'email_backend': forms.TextInput(attrs={'class': 'form-control'}),
            'email_host': forms.TextInput(attrs={'class': 'form-control'}),
            'email_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'email_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_host_user': forms.TextInput(attrs={'class': 'form-control'}),
            'default_from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        email_use_tls = cleaned_data.get('email_use_tls')
        email_use_ssl = cleaned_data.get('email_use_ssl')
        
        if email_use_tls and email_use_ssl:
            raise forms.ValidationError("Cannot use both TLS and SSL at the same time.")
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if not self.cleaned_data.get('email_host_password'):
            instance.email_host_password = self.instance.email_host_password
            
        if commit:
            instance.save()
            
        return instance 