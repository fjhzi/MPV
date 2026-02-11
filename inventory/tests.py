from django.test import Client, TestCase

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import Category, DeviceAppointment, DeviceEvent, MedicalDevice, Room
from .views import MedicalDeviceDetailView


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

    def test_search_finds_by_category_name(self):
        response = self.client.get(reverse("dashboard"), {"q": "EKG"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monitor")

    def test_search_finds_by_room_name(self):
        response = self.client.get(reverse("dashboard"), {"q": "A-101"})
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
    def test_reminder_archive_view_exists(self):
        from .views import ReminderArchiveView

        self.assertIsNotNone(ReminderArchiveView)


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


    def test_reminders_default_shows_all_open_appointments(self):
        DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.MAINTENANCE,
            due_date="2030-01-01",
            completed=False,
        )
        DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.CALIBRATION,
            due_date="2035-01-01",
            completed=False,
        )

        response = self.client.get(reverse("reminders"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["appointments"]), 2)

    def test_archive_shows_only_completed_appointments(self):
        DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.MAINTENANCE,
            due_date="2030-01-01",
            completed=False,
        )
        DeviceAppointment.objects.create(
            medical_device=self.device,
            appointment_type=DeviceAppointment.AppointmentType.CALIBRATION,
            due_date="2030-02-01",
            completed=True,
        )

        response = self.client.get(reverse("reminders-archive"))

        self.assertEqual(response.status_code, 200)
        appointments = response.context["appointments"]
        self.assertEqual(len(appointments), 1)
        self.assertTrue(appointments[0].completed)


class DocumentManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="EKG")
        self.device = MedicalDevice.objects.create(name="Monitor", category=self.category, serial_number="SN-77")

    def test_documents_page_loads(self):
        response = self.client.get(reverse("documents"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dokument hochladen")

    def test_upload_document_from_documents_page(self):
        file = SimpleUploadedFile("manual.txt", b"test content", content_type="text/plain")

        response = self.client.post(
            reverse("documents"),
            {
                "action": "upload_document",
                "category": self.category.id,
                "title": "Anleitung",
                "file": file,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.category.documents.count(), 1)

    def test_documents_page_shows_categories_in_accordion(self):
        response = self.client.get(reverse("documents"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion-button")
        self.assertContains(response, "EKG (0 Dokumente)")

    def test_delete_document_from_documents_page(self):
        document = self.category.documents.create(
            title="Anleitung",
            file=SimpleUploadedFile("manual.txt", b"delete me", content_type="text/plain"),
        )

        response = self.client.post(
            reverse("documents"),
            {
                "action": "delete_document",
                "document_id": document.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.category.documents.filter(id=document.id).exists())

    def test_device_detail_shows_document_delete_button_with_confirmation(self):
        self.category.documents.create(
            title="Anleitung",
            file=SimpleUploadedFile("manual.txt", b"detail", content_type="text/plain"),
        )

        response = self.client.get(reverse("device-detail", kwargs={"pk": self.device.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="action" value="delete_document"')
        self.assertContains(response, "Dokument wirklich löschen?")


class StammdatenPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_stammdaten_has_no_document_upload_section(self):
        response = self.client.get(reverse("stammdaten"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dokument hochladen")


class CategoryAttributesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_category_with_optional_intervals(self):
        response = self.client.post(
            reverse("stammdaten"),
            {
                "action": "create_category",
                "name": "Anästhesie",
                "dguv3_interval_months": 12,
                "mtk_interval_months": 24,
                "stk_interval_months": 36,
                "calibration_interval_months": 18,
            },
        )

        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(name="Anästhesie")
        self.assertEqual(category.dguv3_interval_months, 12)
        self.assertEqual(category.mtk_interval_months, 24)
        self.assertEqual(category.stk_interval_months, 36)
        self.assertEqual(category.calibration_interval_months, 18)

    def test_update_category_intervals(self):
        category = Category.objects.create(name="Intensiv")

        response = self.client.post(
            reverse("stammdaten"),
            {
                "action": "update_category",
                "category_id": category.id,
                f"category_{category.id}-name": "Intensivstation",
                f"category_{category.id}-dguv3_interval_months": 6,
                f"category_{category.id}-mtk_interval_months": 12,
                f"category_{category.id}-stk_interval_months": "",
                f"category_{category.id}-calibration_interval_months": 9,
            },
        )

        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, "Intensivstation")
        self.assertEqual(category.dguv3_interval_months, 6)
        self.assertEqual(category.mtk_interval_months, 12)
        self.assertIsNone(category.stk_interval_months)
        self.assertEqual(category.calibration_interval_months, 9)


class MedicalDeviceFormFieldsTests(TestCase):
    def test_medical_device_form_has_delivery_date_but_no_ce_marking(self):
        response = self.client.get(reverse("device-create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="delivery_date"')
        self.assertNotContains(response, 'name="ce_marking"')


class EventActionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Kardiologie")
        self.device = MedicalDevice.objects.create(name="EKG-Gerät", category=self.category, serial_number="SN-4")

    def test_create_event(self):
        response = self.client.post(
            reverse("event-create", kwargs={"pk": self.device.id}),
            {
                "event_date": "2030-01-10",
                "note": "Gerät umgezogen",
            },
        )

        self.assertEqual(response.status_code, 302)
        event = DeviceEvent.objects.get(medical_device=self.device)
        self.assertEqual(str(event.event_date), "2030-01-10")

    def test_delete_event(self):
        event = DeviceEvent.objects.create(
            medical_device=self.device,
            event_date="2030-01-10",
            note="Alt",
        )

        response = self.client.post(
            reverse("event-delete", kwargs={"device_pk": self.device.id, "event_pk": event.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(DeviceEvent.objects.filter(id=event.id).exists())

    def test_events_sorted_from_newest_to_oldest(self):
        newer = DeviceEvent.objects.create(medical_device=self.device, event_date="2030-02-01", note="Neu")
        older = DeviceEvent.objects.create(medical_device=self.device, event_date="2030-01-01", note="Alt")

        response = self.client.get(reverse("device-detail", kwargs={"pk": self.device.id}))

        self.assertEqual(response.status_code, 200)
        events = list(response.context["events"])
        self.assertEqual(events, [newer, older])


class DeviceDetailViewResilienceTests(TestCase):
    def test_safe_related_list_returns_empty_and_sets_flag_on_database_error(self):
        class BrokenManager:
            def all(self):
                from django.db import DatabaseError

                raise DatabaseError("missing table")

        context = {}
        view = MedicalDeviceDetailView()

        result = view._safe_related_list(
            BrokenManager(),
            missing_table_context_key="events_unavailable",
            context=context,
        )

        self.assertEqual(result, [])
        self.assertTrue(context["events_unavailable"])
