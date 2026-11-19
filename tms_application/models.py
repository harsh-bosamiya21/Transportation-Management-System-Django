from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

class User(AbstractUser):
    is_customer = models.BooleanField('Is customer', default=False)
    is_driver = models.BooleanField('Is driver', default=False)

# Customer Model
class NewCustomer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, help_text="Building, flat, street, area, landmark")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.customer_name

    def full_address(self):
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.pincode:
            parts.append(f"PIN-{self.pincode}")
        return ", ".join(parts) if parts else self.address


# Driver Model
from django.db import models

class NewDriver(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('ST', 'Small Truck'),
        ('FT', 'Flatbed Truck'),
        ('TrR', 'Trailer Truck'),
        ('TkT', 'Tanker Truck'),
        ('CT', 'Container Truck'),
        ('MV', 'Mini Van'),
    ]
    
    AVAILABLE_CHOICES = [
        (True, 'Yes'),
        (False, 'No'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    driver_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    vehicle_type = models.CharField(max_length=3, choices=VEHICLE_TYPE_CHOICES)
    vehicle_registration_number = models.CharField(max_length=50)
    vehicle_number_plate = models.CharField(max_length=20)
    available = models.BooleanField(choices=AVAILABLE_CHOICES)

    def is_fleet_complete(self):
        """Returns True only when driver has fully provided all mandatory vehicle and license specs."""
        return bool(
            self.vehicle_type and
            self.vehicle_registration_number and str(self.vehicle_registration_number).strip() and
            self.vehicle_number_plate and str(self.vehicle_number_plate).strip() and
            self.license_number and str(self.license_number).strip()
        )

    @classmethod
    def get_eligible_drivers(cls):
        """QuerySet of drivers who have completely set up their fleet details, are on-duty, and not booked on active consignments."""
        from django.db.models import Q
        from django.apps import apps
        NewShipmentModel = apps.get_model('tms_application', 'NewShipment')

        # Exclude drivers currently assigned to active, unfinished shipments
        active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']
        busy_driver_ids = NewShipmentModel.objects.filter(
            status__in=active_statuses,
            driver__isnull=False
        ).values_list('driver_id', flat=True)

        return cls.objects.filter(
            available=True
        ).exclude(
            id__in=busy_driver_ids
        ).exclude(
            Q(vehicle_type__isnull=True) | Q(vehicle_type='') |
            Q(vehicle_registration_number__isnull=True) | Q(vehicle_registration_number='') |
            Q(vehicle_number_plate__isnull=True) | Q(vehicle_number_plate='') |
            Q(license_number__isnull=True) | Q(license_number='')
        )

    def __str__(self):
        return self.driver_name



# Shipment Model
class NewShipment(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]

    DESTINATION_CHOICES = [
        ('MI', 'Mumbai'),
        ('DL', 'Delhi'),
        ('AMD', 'Ahmedabad'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(NewCustomer, on_delete=models.CASCADE, blank=True, null=True)
    order_date = models.DateField(blank=True, null=True)
    shipment_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    package_description = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    driver = models.ForeignKey(NewDriver, on_delete=models.SET_NULL, null=True, blank=True)
    truck_type = models.CharField(max_length=10, choices=NewDriver.VEHICLE_TYPE_CHOICES, default='ST', blank=True, null=True)
    from_destination = models.CharField(max_length=255, choices=DESTINATION_CHOICES, default='MI')
    to_destination = models.CharField(max_length=255, choices=DESTINATION_CHOICES, default='DL')

    def __str__(self):
        if self.customer:
            return f"Shipment {self.tracking_id} for {self.customer.customer_name}"
        else:
            return f"Shipment {self.tracking_id} (No customer assigned)"
        


class Package(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]

    sender_name = models.CharField(max_length=100)
    receiver_name = models.CharField(max_length=100)
    receiver_email = models.EmailField()
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tracking_id} - {self.receiver_name}"

