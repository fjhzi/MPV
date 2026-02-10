from django.test import Client, TestCase
from django.urls import reverse

from datetime import timedelta

from django.utils import timezone

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


class ReminderViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name="Reminder-Cat")
        room = Room.objects.create(name="Reminder-Room")
        self.device = MedicalDevice.objects.create(
            name="Reminder-Device",
            category=category,
            room=room,
            serial_number="SN-REM-1",
        )

    def test_reminders_show_all_appointments_without_filter(self):
        today = timezone.localdate()
        overdue = DeviceAppointment.objects.create(medical_device=self.device, due_date=today - timedelta(days=2))
        upcoming = DeviceAppointment.objects.create(medical_device=self.device, due_date=today + timedelta(days=5))
        later = DeviceAppointment.objects.create(medical_device=self.device, due_date=today + timedelta(days=60))

        response = self.client.get(reverse("reminders"), {"date_filter": "overdue"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["appointments"]), [overdue, upcoming, later])
        self.assertNotContains(response, 'name="date_filter"')

    def test_reminders_highlight_overdue_and_due_within_30_days(self):
        today = timezone.localdate()
        overdue = DeviceAppointment.objects.create(medical_device=self.device, due_date=today - timedelta(days=1))
        warning = DeviceAppointment.objects.create(medical_device=self.device, due_date=today + timedelta(days=10))

        response = self.client.get(reverse("reminders"))

        self.assertContains(response, f'<td class="reminder-due-overdue">{overdue.due_date}</td>', html=True)
        self.assertContains(response, f'<td class="reminder-due-warning">{warning.due_date}</td>', html=True)
