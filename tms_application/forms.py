from django import forms
from .models import User
from .models import  NewCustomer, NewDriver, NewShipment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re



class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a strong password"
            }
        )
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password"
            }
        )
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'is_driver', 'is_customer')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
            if len(password2) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password2):
                raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
            if not re.search(r'[a-z]', password2):
                raise ValidationError("Password must contain at least one lowercase letter (a-z).")
            if not re.search(r'\d', password2):
                raise ValidationError("Password must contain at least one number (0-9).")
            if not re.search(r'[@$!%*?&_\-#~^+=<>;:,.]', password2):
                raise ValidationError("Password must contain at least one special character (@$!%*?&_ etc.).")
            validate_password(password2, self.instance)
        return password2




class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)



class CustomerForm(forms.ModelForm):
    class Meta:
        model = NewCustomer
        fields = ['customer_name', 'address', 'city', 'state', 'pincode', 'phone_number', 'email']

class DriverForm(forms.ModelForm):
    class Meta:
        model = NewDriver
        fields = ['driver_name', 'license_number', 'phone_number', 'email', 'vehicle_type', 'vehicle_registration_number', 'vehicle_number_plate', 'available']  # Modify based on your model

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = NewShipment
        exclude = ['tracking_id']

class TrackingForm(forms.Form):
    tracking_id = forms.UUIDField(
         
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your tracking code. e.g. 987733733-GT'}),
    )

