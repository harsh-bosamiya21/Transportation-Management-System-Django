from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import NewShipment

@receiver(post_save, sender=NewShipment)
def handle_shipment_post_save(sender, instance, created, **kwargs):
    # 1. Synchronize driver booking status (book when assigned, release when delivered)
    if instance.driver:
        active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']
        if instance.status in active_statuses:
            if instance.driver.available:
                instance.driver.available = False
                instance.driver.save(update_fields=['available'])
        elif instance.status == 'delivered':
            remaining_active = NewShipment.objects.filter(
                driver=instance.driver,
                status__in=active_statuses
            ).exclude(id=instance.id).exists()
            if not remaining_active and not instance.driver.available:
                instance.driver.available = True
                instance.driver.save(update_fields=['available'])

    # 2. Dispatch status update email notification
    customer_display = instance.customer.customer_name if instance.customer else (instance.user.username if instance.user else "Valued Customer")
    origin = instance.get_from_destination_display() if hasattr(instance, 'get_from_destination_display') else instance.from_destination
    destination = instance.get_to_destination_display() if hasattr(instance, 'get_to_destination_display') else instance.to_destination
    driver_name = instance.driver.driver_name if instance.driver else "Assigned Fleet"
    plate = instance.driver.vehicle_number_plate if (instance.driver and instance.driver.vehicle_number_plate) else "N/A"
    truck_name = instance.get_truck_type_display() if hasattr(instance, 'get_truck_type_display') else instance.truck_type

    if created:
        subject = f"Shipment Registered #{str(instance.tracking_id)[:8]} - TMS"
        message = (
            f"Dear {customer_display},\n\n"
            f"Your consignment has been registered successfully with Transport Management System (TMS).\n\n"
            f"Shipment Details:\n"
            f"  * Tracking ID: {instance.tracking_id}\n"
            f"  * Vehicle Type: {truck_name}\n"
            f"  * Route: {origin} -> {destination}\n"
            f"  * Assigned Driver: {driver_name} (Plate: {plate})\n"
            f"  * Current Status: Processing\n\n"
            f"You can track your live shipment milestone at any time using your tracking ID.\n\n"
            f"Best regards,\n"
            f"Transport Management System Team"
        )
    else:
        subject = f"Delivery Update #{str(instance.tracking_id)[:8]} ({instance.get_status_display()}) - TMS"
        message = (
            f"Dear {customer_display},\n\n"
            f"The status of your consignment #{str(instance.tracking_id)[:8]} has been updated.\n\n"
            f"Current Status: {instance.get_status_display()}\n"
            f"Route: {origin} -> {destination}\n"
            f"Assigned Driver: {driver_name}\n\n"
            f"Tracking ID: {instance.tracking_id}\n\n"
            f"Best regards,\n"
            f"Transport Management System Team"
        )
    
    recipient_email = None
    if instance.customer and instance.customer.email:
        recipient_email = instance.customer.email
    elif instance.user and instance.user.email:
        recipient_email = instance.user.email

    if recipient_email:
        try:
            from django.conf import settings
            from_email = getattr(settings, 'EMAIL_HOST_USER', 'tmsdjango@gmail.com')
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],
                fail_silently=True,
            )
        except Exception:
            pass


@receiver(post_delete, sender=NewShipment)
def handle_shipment_post_delete(sender, instance, **kwargs):
    # If an assigned active shipment is deleted, release driver back to available
    if instance.driver:
        active_statuses = ['processing', 'shipped', 'in_transit', 'out_for_delivery']
        has_active = NewShipment.objects.filter(
            driver=instance.driver,
            status__in=active_statuses
        ).exists()
        if not has_active and not instance.driver.available:
            instance.driver.available = True
            instance.driver.save(update_fields=['available'])
