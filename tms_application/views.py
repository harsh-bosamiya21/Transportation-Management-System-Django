from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from .forms import CustomerForm, DriverForm, ShipmentForm, TrackingForm, ContactForm, SignUpForm
from .models import NewShipment, NewCustomer, NewDriver,  Package  # Import your models
import uuid
import json




# Create your views here.
def index(request):
    return render(request, "index.html")

# Helper to locate or link NewDriver profile for logged-in user
def get_driver_for_user(user):
    """Helper to locate or link NewDriver profile for logged-in user"""
    if not user.is_authenticated:
        return None
    # 1. By direct foreign key link
    driver = NewDriver.objects.filter(user=user).first()
    if driver:
        return driver
    # 2. By matching driver_name with username
    driver = NewDriver.objects.filter(driver_name__iexact=user.username).first()
    if driver:
        if not driver.user:
            driver.user = user
            driver.save(update_fields=['user'])
        return driver
    # 3. By matching email
    if user.email:
        driver = NewDriver.objects.filter(email__iexact=user.email).first()
        if driver:
            if not driver.user:
                driver.user = user
                driver.save(update_fields=['user'])
            return driver
    # 4. Fallback if single driver exists without user linked
    if NewDriver.objects.count() == 1:
        single_driver = NewDriver.objects.first()
        if not single_driver.user:
            single_driver.user = user
            single_driver.save(update_fields=['user'])
        return single_driver
    return None


def home(request):
    driver_profile = None
    is_fleet_complete = False
    customer_profile = None
    is_customer_profile_complete = False
    admin_stats = None

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            role = 'admin'
            admin_stats = {
                'total_users': User.objects.count(),
                'total_customers': NewCustomer.objects.count(),
                'total_drivers': NewDriver.objects.count(),
                'active_drivers': NewDriver.objects.filter(available=True).count(),
                'total_shipments': NewShipment.objects.count(),
                'active_shipments': NewShipment.objects.filter(status__in=['processing', 'shipped', 'in_transit', 'out_for_delivery']).count(),
                'delivered_shipments': NewShipment.objects.filter(status='delivered').count(),
            }
        elif getattr(request.user, 'is_customer', False):
            role = 'customer'
            customer_profile = NewCustomer.objects.filter(user=request.user).first()
            if customer_profile:
                is_customer_profile_complete = bool(
                    customer_profile.state and customer_profile.city and customer_profile.address
                )
        elif getattr(request.user, 'is_driver', False):
            role = 'driver'
            driver_profile = get_driver_for_user(request.user)
            if driver_profile:
                is_fleet_complete = driver_profile.is_fleet_complete()
        else:
            role = 'guest'
    else:
        role = 'guest'

    return render(request, 'home.html', {
        'role': role,
        'driver_profile': driver_profile,
        'is_fleet_complete': is_fleet_complete,
        'customer_profile': customer_profile,
        'is_customer_profile_complete': is_customer_profile_complete,
        'admin_stats': admin_stats,
    })

def about(request):
    return render(request, "about.html")

def services(request):
    return render(request, "services.html")

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Send email
            try:
                from django.conf import settings
                support_email = getattr(settings, 'EMAIL_HOST_USER', 'tmsdjango@gmail.com')
                send_mail(
                    f'[TMS Inquiry] {subject} - From {name}',  # Subject
                    f'{message} \n\nSender Email: {email}',     # Message
                    support_email,                              # From email
                    [support_email],                            # To support email
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, "Your message has been sent successfully. Thank you!")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html')

def pricing(request):
    return render(request, "pricing.html")

def manage_truck_driver(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if getattr(request.user, 'is_driver', False):
        return redirect('driver_deliveries')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/tms_application/newdriver/')
    return redirect('home')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Log the user in
            auth_login(request, user)
            return redirect('home')
        else:
            error = 'Invalid username or password. Please check your credentials.'
            messages.error(request, error)
            return render(request, 'login.html', {'error': error, 'username': username})

    return render(request, 'login.html')


User = get_user_model()

def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'customer')

        # Validate form inputs
        if not username or not email or not password:
            error = "Username, email address, and password are all required."
            messages.error(request, error)
            return render(request, 'sign_up.html', {'error': error, 'username': username, 'email': email, 'role': role})

        # Validate email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            error = "Please enter a valid email address (e.g. user@example.com)."
            messages.error(request, error)
            return render(request, 'sign_up.html', {'error': error, 'username': username, 'email': email, 'role': role})

        # Check if username already exists in database (prevents IntegrityError crash)
        if User.objects.filter(username__iexact=username).exists():
            error = f"The username '{username}' is already taken. Please choose another username or log in."
            messages.error(request, error)
            return render(request, 'sign_up.html', {'error': error, 'username': username, 'email': email, 'role': role})

        # Check if email is already registered in database
        if User.objects.filter(email__iexact=email).exists():
            error = f"An account with email '{email}' already exists. Please log in or use a different email."
            messages.error(request, error)
            return render(request, 'sign_up.html', {'error': error, 'username': username, 'email': email, 'role': role})

        try:
            # Hash the password before saving to the database
            hashed_password = make_password(password)

            # Create a new user with email
            user = User(username=username, email=email, password=hashed_password)

            # Set the role
            if role == 'customer':
                user.is_customer = True
            elif role == 'driver':
                user.is_driver = True

            # Save the user to the database
            user.save()

            # Initialize or link the role profile with the registered email
            if role == 'customer':
                customer_profile = NewCustomer.objects.filter(user=user).first() or \
                                   NewCustomer.objects.filter(customer_name__iexact=username).first()
                if customer_profile:
                    customer_profile.user = user
                    customer_profile.email = email
                    customer_profile.save(update_fields=['user', 'email'])
                else:
                    NewCustomer.objects.create(
                        user=user,
                        customer_name=username,
                        email=email,
                        phone_number='',
                        address='',
                        city='',
                        state='',
                        pincode=''
                    )
            elif role == 'driver':
                driver_profile = NewDriver.objects.filter(user=user).first() or \
                                 NewDriver.objects.filter(driver_name__iexact=username).first() or \
                                 NewDriver.objects.filter(email__iexact=email).first()
                if driver_profile:
                    driver_profile.user = user
                    driver_profile.email = email
                    driver_profile.save(update_fields=['user', 'email'])
                else:
                    NewDriver.objects.create(
                        user=user,
                        driver_name=username,
                        email=email,
                        license_number='',
                        phone_number='',
                        vehicle_type='',
                        vehicle_registration_number='',
                        vehicle_number_plate='',
                        available=True
                    )

            messages.success(request, f"Account '{username}' created successfully! Please log in.")
            return redirect('login')
        except Exception as e:
            error = f"Could not create account: {str(e)}"
            messages.error(request, error)
            return render(request, 'sign_up.html', {'error': error, 'username': username, 'email': email, 'role': role})

    return render(request, 'sign_up.html')



# List of Indian States and Union Territories
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

# View to manage and update the logged-in customer's profile details
def add_customer(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to manage your customer profile.")
        return redirect('login')

    # Look for existing customer profile for this user
    existing_customer = NewCustomer.objects.filter(user=request.user).first() or \
                        NewCustomer.objects.filter(customer_name__iexact=request.user.username).first()

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        state = request.POST.get('state', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()  # Building, flat, street, area, landmark
        pincode = request.POST.get('pincode', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()

        # Validation
        if len(phone_number) != 10 or not phone_number.isdigit():
            error = "Please enter a valid 10-digit mobile number."
            messages.error(request, error)
            return render(request, 'add_customer.html', {
                'error': error,
                'existing_customer': existing_customer,
                'indian_states': INDIAN_STATES,
            })

        if existing_customer:
            # Update single customer profile
            existing_customer.customer_name = customer_name
            existing_customer.state = state
            existing_customer.city = city
            existing_customer.address = address
            existing_customer.pincode = pincode
            existing_customer.phone_number = phone_number
            existing_customer.email = email
            if not existing_customer.user:
                existing_customer.user = request.user
            existing_customer.save()
            messages.success(request, "Customer profile and delivery details updated successfully!")
        else:
            # Create single customer profile for this user
            NewCustomer.objects.create(
                user=request.user,
                customer_name=customer_name,
                state=state,
                city=city,
                address=address,
                pincode=pincode,
                phone_number=phone_number,
                email=email
            )
            messages.success(request, "Customer profile details saved successfully!")

        return redirect('home')

    return render(request, 'add_customer.html', {
        'existing_customer': existing_customer,
        'indian_states': INDIAN_STATES,
    })


# View to handle adding or updating driver fleet profile
def add_driver(request):
    driver_profile = get_driver_for_user(request.user) if request.user.is_authenticated else None

    if request.method == 'POST':
        driver_name = request.POST.get('driver_name', '').strip()
        license_number = request.POST.get('license_number', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        vehicle_type = request.POST.get('vehicle_type', '').strip()
        vehicle_registration_number = request.POST.get('vehicle_registration_number', '').strip()
        vehicle_number_plate = request.POST.get('vehicle_number_plate', '').strip()
        available_val = request.POST.get('available')
        if available_val is not None:
            available = (available_val.strip().lower() in ['true', '1', 'yes', 'on'])
        else:
            available = True

        if driver_profile:
            # Update existing driver record
            driver_profile.driver_name = driver_name
            driver_profile.license_number = license_number
            driver_profile.phone_number = phone_number
            driver_profile.email = email
            driver_profile.vehicle_type = vehicle_type
            driver_profile.vehicle_registration_number = vehicle_registration_number
            driver_profile.vehicle_number_plate = vehicle_number_plate
            driver_profile.available = available
            driver_profile.save()
            driver = driver_profile
        else:
            # Create new driver record
            driver = NewDriver.objects.create(
                user=request.user if request.user.is_authenticated else None,
                driver_name=driver_name,
                license_number=license_number,
                phone_number=phone_number,
                email=email,
                vehicle_type=vehicle_type,
                vehicle_registration_number=vehicle_registration_number,
                vehicle_number_plate=vehicle_number_plate,
                available=available
            )

        if driver.is_fleet_complete():
            return redirect('driver_deliveries')
        else:
            return redirect('add_driver')

    return render(request, 'add_driver.html', {
        'existing_driver': driver_profile,
    })


# View to quickly toggle driver on-duty / off-duty availability status
def toggle_driver_duty(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to manage your driver status.")
        return redirect('login')
    driver = get_driver_for_user(request.user)
    if not driver:
        messages.error(request, "No fleet driver profile found.")
        return redirect('add_driver')
    
    if not driver.is_fleet_complete():
        messages.warning(request, "Please complete your fleet details (truck type, registration, license) before going On Duty.")
        return redirect('add_driver')

    active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']
    has_active_consignments = NewShipment.objects.filter(driver=driver, status__in=active_statuses).exists()
    if has_active_consignments:
        messages.info(request, "You are currently booked on an active consignment. Your status will automatically return to Available once you mark your delivery completed.")
        return redirect('driver_deliveries')

    driver.available = not driver.available
    driver.save(update_fields=['available'])
    status_text = "On Duty & Ready for Dispatch" if driver.available else "Off Duty"
    messages.success(request, f"Duty status updated: You are now {status_text}.")
    return redirect('driver_deliveries')

TRUCK_METADATA = {
    'ST': {
        'name': 'Small Truck',
        'capacity': 'Up to 2.5 Tons',
        'desc': 'Ideal for intra-city parcels, light cargo, packaged cartons & boxes',
        'icon': 'bi-truck',
        'badge': 'Light Freight'
    },
    'FT': {
        'name': 'Flatbed Truck',
        'capacity': 'Up to 10 Tons',
        'desc': 'Open-deck design for machinery, steel pipes, timber & heavy industrial equipment',
        'icon': 'bi-truck-flatbed',
        'badge': 'Heavy Open Deck'
    },
    'TrR': {
        'name': 'Trailer Truck',
        'capacity': 'Up to 25 Tons',
        'desc': 'Multi-axle long-haul transport for massive multi-ton commercial consignments',
        'icon': 'bi-truck',
        'badge': 'Long-Haul Freight'
    },
    'TkT': {
        'name': 'Tanker Truck',
        'capacity': 'Up to 15,000 Liters',
        'desc': 'Specialized sealed cylindrical tank for liquids, fuels, dairy & chemical cargo',
        'icon': 'bi-fuel-pump-fill',
        'badge': 'Liquid & Bulk'
    },
    'CT': {
        'name': 'Container Truck',
        'capacity': 'Up to 20 Tons (20ft / 40ft)',
        'desc': 'Weather-sealed intermodal container for high-security maritime & domestic cargo',
        'icon': 'bi-box-seam-fill',
        'badge': 'Secure Container'
    },
    'MV': {
        'name': 'Mini Van',
        'capacity': 'Up to 1 Ton',
        'desc': 'Agile express courier van for small shipments & urgent local deliveries',
        'icon': 'bi-car-front-fill',
        'badge': 'Express Courier'
    },
}

def get_truck_options_summary():
    """Returns a list of truck types with metadata and real-time available driver counts."""
    options = []
    for code, label in NewDriver.VEHICLE_TYPE_CHOICES:
        meta = TRUCK_METADATA.get(code, {})
        eligible_qs = NewDriver.get_eligible_drivers().filter(vehicle_type=code)
        count = eligible_qs.count()
        first_driver = eligible_qs.first()
        options.append({
            'code': code,
            'name': label,
            'capacity': meta.get('capacity', 'Standard Payload'),
            'desc': meta.get('desc', ''),
            'icon': meta.get('icon', 'bi-truck'),
            'badge': meta.get('badge', 'Freight'),
            'available_count': count,
            'first_driver_name': first_driver.driver_name if first_driver else None,
            'first_driver_plate': (first_driver.vehicle_number_plate or first_driver.vehicle_registration_number) if first_driver else None,
        })
    return options

# View to handle adding a shipment
def add_shipment(request):
    # Require authentication for booking shipment
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to book a shipment.")
        return redirect('login')

    # Drivers cannot book customer shipments
    if getattr(request.user, 'is_driver', False):
        messages.warning(request, "Driver accounts cannot book shipments. Access your active dispatch console here.")
        return redirect('driver_deliveries')

    # Automatically resolve or initialize logged-in user's single customer profile
    user_customer = NewCustomer.objects.filter(user=request.user).first()
    if not user_customer:
        user_customer = NewCustomer.objects.filter(customer_name__iexact=request.user.username).first()
        if user_customer and not user_customer.user:
            user_customer.user = request.user
            user_customer.save(update_fields=['user'])

    if not user_customer:
        user_customer = NewCustomer.objects.create(
            user=request.user,
            customer_name=request.user.username,
            email=request.user.email or f"{request.user.username}@tms.local",
            phone_number="",
            address="",
            city="",
            state="",
            pincode=""
        )

    is_customer_profile_complete = bool(
        user_customer.state and user_customer.city and user_customer.address
    )

    truck_options = get_truck_options_summary()
    truck_options_json = json.dumps(truck_options)

    # Handle form submission
    if request.method == 'POST':
        truck_type = request.POST.get('truck_type')
        order_date = request.POST.get('order_date')
        shipment_date = request.POST.get('shipment_date')
        package_description = request.POST.get('package_description')
        quantity = request.POST.get('quantity')
        from_destination = request.POST.get('from_destination')
        to_destination = request.POST.get('to_destination')
        tracking_id = uuid.uuid4()

        valid_truck_codes = [c[0] for c in NewDriver.VEHICLE_TYPE_CHOICES]
        if not truck_type or truck_type not in valid_truck_codes:
            truck_type = 'ST'

        # Check driver availability for the requested truck type
        eligible_for_truck = NewDriver.get_eligible_drivers().filter(vehicle_type=truck_type)
        assigned_driver = eligible_for_truck.first()

        # VALIDATION: Ensure an eligible driver with the requested truck type is available
        if not assigned_driver:
            truck_name = dict(NewDriver.VEHICLE_TYPE_CHOICES).get(truck_type, truck_type)
            available_truck_names = [
                opt['name'] for opt in truck_options if opt['available_count'] > 0
            ]
            if available_truck_names:
                error_msg = f"Booking Failed: No verified driver with a '{truck_name}' is currently on-duty and available. Currently available truck types in fleet: {', '.join(available_truck_names)}. Please choose an available truck type."
            else:
                error_msg = f"Booking Failed: No fleet drivers with a '{truck_name}' are currently available on-duty. Drivers must enroll and verify their fleet details to receive consignments."

            messages.error(request, error_msg)
            return render(request, 'add_shipment.html', {
                'user_customer': user_customer,
                'is_customer_profile_complete': is_customer_profile_complete,
                'truck_options': truck_options,
                'truck_options_json': truck_options_json,
                'selected_truck_type': truck_type,
                'error': error_msg,
                'form_data': request.POST,
            })

        # Customer is directly taken from the logged-in user's profile
        customer = user_customer

        # Create a new shipment instance with chosen truck type and matched driver
        new_shipment = NewShipment(
            user=request.user,
            customer=customer,
            truck_type=truck_type,
            driver=assigned_driver,
            order_date=order_date,
            shipment_date=shipment_date,
            package_description=package_description,
            quantity=quantity,
            from_destination=from_destination,
            to_destination=to_destination,
            tracking_id=tracking_id,
            status='processing'
        )
        new_shipment.save()

        # Book the assigned driver and remove them from available dispatch pool until job is finished
        if assigned_driver:
            assigned_driver.available = False
            assigned_driver.save(update_fields=['available'])

        messages.success(
            request,
            f"Shipment booked successfully! Requested vehicle: {assigned_driver.get_vehicle_type_display()}. Assigned fleet driver: {assigned_driver.driver_name} (Plate: {assigned_driver.vehicle_number_plate}). Tracking ID: {tracking_id}"
        )

        return redirect('order_history')

    return render(request, 'add_shipment.html', {
        'user_customer': user_customer,
        'is_customer_profile_complete': is_customer_profile_complete,
        'truck_options': truck_options,
        'truck_options_json': truck_options_json,
        'selected_truck_type': 'ST',
    })



# Tracking view with vertical stepper data
def track(request):
    shipment = None
    tracking_id = request.GET.get('tracking_id')
    if not tracking_id and request.method == 'POST':
        tracking_id = request.POST.get('tracking_id')

    if tracking_id:
        tracking_id = str(tracking_id).strip()
        try:
            shipment = NewShipment.objects.filter(tracking_id=tracking_id).first()
            if not shipment:
                messages.error(request, f"No shipment found matching tracking ID: {tracking_id}")
        except Exception:
            messages.error(request, "Invalid tracking ID format. Please check the code and try again.")

    form = TrackingForm(initial={'tracking_id': tracking_id} if tracking_id else None)

    # Status sequence for vertical progress bar (1 to 5)
    status_order = {
        'processing': 1,
        'shipped': 2,
        'in_transit': 3,
        'out_for_delivery': 4,
        'delivered': 5,
    }
    current_step = status_order.get(shipment.status, 1) if shipment else 0

    return render(request, 'track.html', {
        'form': form,
        'shipment': shipment,
        'current_step': current_step,
        'tracking_id': tracking_id,
    })


# Driver: View Active Assigned Deliveries & Update Status
def driver_deliveries(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access driver deliveries.")
        return redirect('login')

    if not getattr(request.user, 'is_driver', False):
        messages.warning(request, "Access restricted to driver accounts only.")
        return redirect('home')

    from django.db.models import Q
    driver_profile = get_driver_for_user(request.user)
    is_fleet_complete = driver_profile.is_fleet_complete() if driver_profile else False

    # Active deliveries: in processing, shipped, in_transit, out_for_delivery
    active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']

    if driver_profile:
        shipments = NewShipment.objects.filter(
            Q(driver=driver_profile) | Q(driver__user=request.user) | Q(driver__driver_name__iexact=request.user.username),
            status__in=active_statuses
        ).distinct().order_by('-order_date', '-id')
    else:
        shipments = NewShipment.objects.filter(
            Q(driver__user=request.user) | Q(driver__driver_name__iexact=request.user.username) | Q(user=request.user),
            status__in=active_statuses
        ).distinct().order_by('-order_date', '-id')

    total_active = shipments.count()
    in_transit_count = shipments.filter(status='in_transit').count()
    out_for_delivery_count = shipments.filter(status='out_for_delivery').count()
    pending_count = shipments.filter(status__in=['processing', 'shipped']).count()

    return render(request, 'driver_deliveries.html', {
        'driver': driver_profile,
        'is_fleet_complete': is_fleet_complete,
        'shipments': shipments,
        'total_active': total_active,
        'in_transit_count': in_transit_count,
        'out_for_delivery_count': out_for_delivery_count,
        'pending_count': pending_count,
        'status_choices': NewShipment.STATUS_CHOICES,
    })


# Driver: Update Status of an Assigned Delivery
def update_delivery_status(request, shipment_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to perform this action.")
        return redirect('login')

    if not getattr(request.user, 'is_driver', False):
        messages.error(request, "Only drivers are permitted to update shipment delivery status.")
        return redirect('home')

    if request.method == 'POST':
        shipment = get_object_or_404(NewShipment, id=shipment_id)
        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in NewShipment.STATUS_CHOICES]

        if new_status in valid_statuses:
            old_label = shipment.get_status_display()
            shipment.status = new_status
            if new_status == 'delivered':
                from django.utils import timezone
                shipment.shipment_date = timezone.now().date()
            shipment.save()

            # When shipment is delivered, check if driver has finished all active jobs and unbook them
            if new_status == 'delivered' and shipment.driver:
                active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']
                has_remaining_active = NewShipment.objects.filter(
                    driver=shipment.driver,
                    status__in=active_statuses
                ).exclude(id=shipment.id).exists()
                if not has_remaining_active and not shipment.driver.available:
                    shipment.driver.available = True
                    shipment.driver.save(update_fields=['available'])

            messages.success(
                request,
                f"Delivery #{str(shipment.tracking_id)[:8]} status updated to '{shipment.get_status_display()}' successfully!"
            )
            if new_status == 'delivered':
                return redirect('driver_history')
        else:
            messages.error(request, "Invalid status choice selected.")

    return redirect('driver_deliveries')


# Driver: Past Delivery History
def driver_history(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your delivery history.")
        return redirect('login')

    if not getattr(request.user, 'is_driver', False):
        messages.warning(request, "Delivery history is only accessible by drivers.")
        return redirect('home')

    from django.db.models import Q, Sum
    driver_profile = get_driver_for_user(request.user)

    if driver_profile:
        completed_shipments = NewShipment.objects.filter(
            Q(driver=driver_profile) | Q(driver__user=request.user) | Q(driver__driver_name__iexact=request.user.username),
            status='delivered'
        ).distinct().order_by('-shipment_date', '-id')
    else:
        completed_shipments = NewShipment.objects.filter(
            Q(driver__user=request.user) | Q(driver__driver_name__iexact=request.user.username) | Q(user=request.user),
            status='delivered'
        ).distinct().order_by('-shipment_date', '-id')

    total_completed = completed_shipments.count()
    total_packages = completed_shipments.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

    return render(request, 'driver_history.html', {
        'driver': driver_profile,
        'shipments': completed_shipments,
        'total_completed': total_completed,
        'total_packages': total_packages,
    })


# Customer: Individual Order History (Only for customers)
def order_history(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your order history.")
        return redirect('login')

    # If user is a driver, redirect them to their dedicated assigned deliveries page
    if getattr(request.user, 'is_driver', False):
        return redirect('driver_deliveries')

    from django.db.models import Q

    # Customer view: show orders booked by this customer
    shipments = NewShipment.objects.filter(
        Q(user=request.user) |
        Q(customer__user=request.user) |
        Q(customer__customer_name__iexact=request.user.username)
    ).distinct().order_by('-order_date', '-id')

    # Summary metrics
    total_orders = shipments.count()
    delivered_orders = shipments.filter(status='delivered').count()
    in_transit_orders = shipments.filter(status__in=['in_transit', 'out_for_delivery']).count()
    processing_orders = shipments.filter(status__in=['processing', 'shipped']).count()

    return render(request, 'order_history.html', {
        'shipments': shipments,
        'role_type': 'customer',
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'in_transit_orders': in_transit_orders,
        'processing_orders': processing_orders,
    })



