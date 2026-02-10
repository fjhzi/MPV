from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, DeviceAppointment, MedicalDevice, Room


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name="EKG")
        room = Room.objects.create(name="A-101")
        MedicalDevice.objects.create(name="Monitor", category=category, room=room, serial_number="SN-1")

    def test_dashboard_loads(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monitor")

    def test_search_filters_devices(self):
        response = self.client.get(reverse("dashboard"), {"q": "SN-1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monitor")


class StammdatenDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Infusion")
        self.room = Room.objects.create(name="B-202")

    def test_staff_can_delete_category(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(username="admin", password="secret", is_staff=True)
        self.client.force_login(user)

        response = self.client.post(reverse("stammdaten"), {"action": "delete_category", "category_id": self.category.id})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_staff_can_delete_room(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(username="admin", password="secret", is_staff=True)
        self.client.force_login(user)

        response = self.client.post(reverse("stammdaten"), {"action": "delete_room", "room_id": self.room.id})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Room.objects.filter(id=self.room.id).exists())

    def test_non_staff_cannot_delete_category(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(username="user", password="secret", is_staff=False)
        self.client.force_login(user)

        response = self.client.post(reverse("stammdaten"), {"action": "delete_category", "category_id": self.category.id})

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())


class AppointmentActionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Labor")
        self.device = MedicalDevice.objects.create(name="Pump", category=self.category, serial_number="SN-2")

    def test_create_appointment_defaults_to_incomplete(self):
        response = self.client.post(
            reverse("appointment-create", kwargs={"pk": self.device.id}),
            {
                "appointment_type": DeviceAppointment.AppointmentType.MAINTENANCE,
                "due_date": "2030-01-01",
                "note": "jährlich",
            },
        )

        self.assertEqual(response.status_code, 302)
        appointment = DeviceAppointment.objects.get(medical_device=self.device)
        self.assertFalse(appointment.completed)

    def test_toggle_complete_updates_appointment(self):
        appointment = DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.CALIBRATION,
            due_date="2030-01-01",
            completed=False,
        )

        response = self.client.post(
            reverse(
                "appointment-toggle-complete",
                kwargs={"device_pk": self.device.id, "appointment_pk": appointment.id},
            )
        )

        self.assertEqual(response.status_code, 302)
        appointment.refresh_from_db()
        self.assertTrue(appointment.completed)

    def test_delete_appointment_removes_it(self):
        appointment = DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.CALIBRATION,
            due_date="2030-01-01",
        )

        response = self.client.post(
            reverse(
                "appointment-delete",
                kwargs={"device_pk": self.device.id, "appointment_pk": appointment.id},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(DeviceAppointment.objects.filter(id=appointment.id).exists())


class CompatibilityTests(TestCase):
    def test_reminder_archive_view_compatibility_alias_exists(self):
        from .views import ReminderArchiveView, ReminderView

        self.assertTrue(issubclass(ReminderArchiveView, ReminderView))


class ReminderViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name="Radiologie")
        self.device = MedicalDevice.objects.create(name="CT", category=category, serial_number="SN-3")

    def test_reminders_page_loads_with_default_filter(self):
        DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.MAINTENANCE,
            due_date="2030-01-01",
            completed=False,
        )

        response = self.client.get(reverse("reminders"))

        self.assertEqual(response.status_code, 200)
