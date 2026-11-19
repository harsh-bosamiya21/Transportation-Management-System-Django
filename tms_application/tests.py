from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import NewCustomer, NewDriver, NewShipment
import uuid

User = get_user_model()

class TmsCoreWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test customer user
        self.customer_user = User.objects.create_user(
            username='test_customer',
            email='customer@example.com',
            password='Password123!',
            is_customer=True
        )
        self.customer_profile = NewCustomer.objects.create(
            user=self.customer_user,
            customer_name='Test Customer Company',
            address='101 Logistic Park, NH-8',
            city='Ahmedabad',
            state='Gujarat',
            pincode='380001',
            phone_number='9876543210',
            email='customer@example.com'
        )

        # Create test driver user
        self.driver_user = User.objects.create_user(
            username='test_driver',
            email='driver@example.com',
            password='Password123!',
            is_driver=True
        )
        self.driver_profile = NewDriver.objects.create(
            user=self.driver_user,
            driver_name='Ramesh Kumar',
            license_number='GJ0120200012345',
            phone_number='9123456780',
            email='driver@example.com',
            vehicle_type='ST',
            vehicle_registration_number='GJ01AB1234',
            vehicle_number_plate='GJ-01-AB-1234',
            available=True
        )

    def test_customer_address_formatting(self):
        """Verifies full address serialization for Indian customer profile."""
        formatted = self.customer_profile.full_address()
        self.assertIn('101 Logistic Park', formatted)
        self.assertIn('Ahmedabad', formatted)
        self.assertIn('Gujarat', formatted)
        self.assertIn('PIN-380001', formatted)

    def test_driver_fleet_completeness(self):
        """Driver must only be verified and eligible when all fleet details are present."""
        self.assertTrue(self.driver_profile.is_fleet_complete())

        # Incomplete driver test
        incomplete_driver = NewDriver.objects.create(
            driver_name='Incomplete Driver',
            license_number='',
            phone_number='9000000000',
            email='inc@example.com',
            vehicle_type='ST',
            vehicle_registration_number='',
            vehicle_number_plate='',
            available=True
        )
        self.assertFalse(incomplete_driver.is_fleet_complete())

    def test_driver_eligibility_and_dispatch_locking(self):
        """Eligible drivers query must exclude drivers booked on active shipments."""
        eligible = NewDriver.get_eligible_drivers().filter(vehicle_type='ST')
        self.assertIn(self.driver_profile, eligible)

        # Create an active shipment assigned to this driver
        shipment = NewShipment.objects.create(
            user=self.customer_user,
            customer=self.customer_profile,
            driver=self.driver_profile,
            truck_type='ST',
            from_destination='AMD',
            to_destination='MI',
            status='processing'
        )

        # Post-save signal should lock driver availability
        self.driver_profile.refresh_from_db()
        self.assertFalse(self.driver_profile.available)

        # Driver should now be excluded from eligible dispatch pool
        eligible_now = NewDriver.get_eligible_drivers().filter(vehicle_type='ST')
        self.assertNotIn(self.driver_profile, eligible_now)

        # Deliver shipment: driver must automatically unlock
        shipment.status = 'delivered'
        shipment.save()

        self.driver_profile.refresh_from_db()
        self.assertTrue(self.driver_profile.available)

    def test_public_tracking_view(self):
        """Public tracking page should find valid shipment by UUID without requiring authentication."""
        tracking_code = uuid.uuid4()
        shipment = NewShipment.objects.create(
            user=self.customer_user,
            customer=self.customer_profile,
            driver=self.driver_profile,
            truck_type='ST',
            from_destination='AMD',
            to_destination='DL',
            tracking_id=tracking_code,
            status='in_transit'
        )

        response = self.client.get(reverse('track'), {'tracking_id': str(tracking_code)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(tracking_code))

    def test_manage_truck_driver_safe_redirect(self):
        """The /manage/ URL should not crash with missing template, but redirect safely."""
        # Unauthenticated: redirects to login
        res = self.client.get(reverse('manage'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('login', res.url)

        # Driver: redirects to driver_deliveries
        self.client.login(username='test_driver', password='Password123!')
        res_driver = self.client.get(reverse('manage'))
        self.assertEqual(res_driver.status_code, 302)
        self.assertEqual(res_driver.url, reverse('driver_deliveries'))

    def test_signup_password_too_short(self):
        """Rejects passwords shorter than 8 characters."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser1',
            'email': 'newuser1@example.com',
            'password': 'Pass1!',
            'confirm_password': 'Pass1!',
            'role': 'customer'
        })
        # Should re-render signup with error, not redirect to login
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Password must be at least 8 characters long")
        self.assertFalse(User.objects.filter(username='newuser1').exists())

    def test_signup_password_missing_uppercase(self):
        """Rejects passwords without an uppercase letter."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'password123!',
            'confirm_password': 'password123!',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "uppercase letter")
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_signup_password_missing_lowercase(self):
        """Rejects passwords without a lowercase letter."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser3',
            'email': 'newuser3@example.com',
            'password': 'PASSWORD123!',
            'confirm_password': 'PASSWORD123!',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "lowercase letter")
        self.assertFalse(User.objects.filter(username='newuser3').exists())

    def test_signup_password_missing_number(self):
        """Rejects passwords without a digit."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser4',
            'email': 'newuser4@example.com',
            'password': 'Password!xyz',
            'confirm_password': 'Password!xyz',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "number (0-9)")
        self.assertFalse(User.objects.filter(username='newuser4').exists())

    def test_signup_password_missing_special_char(self):
        """Rejects passwords without a special character."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser5',
            'email': 'newuser5@example.com',
            'password': 'Password1234',
            'confirm_password': 'Password1234',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "special character")
        self.assertFalse(User.objects.filter(username='newuser5').exists())

    def test_signup_password_mismatch(self):
        """Rejects registration when confirm_password does not match password."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'newuser6',
            'email': 'newuser6@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'DifferentPassword123!',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Passwords do not match")
        self.assertFalse(User.objects.filter(username='newuser6').exists())

    def test_signup_strong_password_success(self):
        """Accepts strong password and creates account successfully."""
        res = self.client.post(reverse('sign_up'), {
            'username': 'stronguser',
            'email': 'stronguser@example.com',
            'password': 'SecureP@ssw0rd2026',
            'confirm_password': 'SecureP@ssw0rd2026',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 302)
        self.assertIn('login', res.url)
        self.assertTrue(User.objects.filter(username='stronguser').exists())

    def test_forgot_password_page_renders(self):
        """Forgot password page should load with 200 OK."""
        res = self.client.get(reverse('forgot_password'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Forgot Password")

    def test_forgot_password_unknown_user(self):
        """Submitting non-existent email/username shows error."""
        res = self.client.post(reverse('forgot_password'), {
            'identifier': 'nonexistent@example.com'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "No account found matching")

    def test_forgot_password_valid_user(self):
        """Submitting registered customer email renders success and generates reset token."""
        res = self.client.post(reverse('forgot_password'), {
            'identifier': 'customer@example.com'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Reset Link Generated")

    def test_reset_password_invalid_token(self):
        """Invalid token should be rejected on reset password page."""
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uidb64 = urlsafe_base64_encode(force_bytes(self.customer_user.pk))
        res = self.client.get(reverse('reset_password', kwargs={'uidb64': uidb64, 'token': 'invalid-token-xyz'}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "invalid or has expired")

    def test_reset_password_success(self):
        """Valid token resets user password and verifies login with new password."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uidb64 = urlsafe_base64_encode(force_bytes(self.customer_user.pk))
        token = default_token_generator.make_token(self.customer_user)

        # POST new strong password
        new_pass = "BrandNewP@ssw0rd2026!"
        res = self.client.post(
            reverse('reset_password', kwargs={'uidb64': uidb64, 'token': token}),
            {'password': new_pass, 'confirm_password': new_pass}
        )
        self.assertEqual(res.status_code, 302)
        self.assertIn('login', res.url)

        # Verify old password no longer works
        self.customer_user.refresh_from_db()
        self.assertFalse(self.customer_user.check_password('Password123!'))

        # Verify new password works
        self.assertTrue(self.customer_user.check_password(new_pass))
