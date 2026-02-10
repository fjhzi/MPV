from django.core.validators import FileExtensionValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class MedicalDevice(models.Model):
    class ActivityStatus(models.TextChoices):
        ACTIVE = "active", "Aktiv"
        INACTIVE = "inactive", "Nicht aktiv"

    class FunctionalStatus(models.TextChoices):
        FUNCTIONAL = "functional", "Funktionsfähig"
        DEFECTIVE = "defective", "Defekt"

    name = models.CharField(max_length=180)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="devices")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="devices")
    activity_status = models.CharField(max_length=20, choices=ActivityStatus.choices, default=ActivityStatus.ACTIVE)
    functional_status = models.CharField(max_length=20, choices=FunctionalStatus.choices, default=FunctionalStatus.FUNCTIONAL)
    serial_number = models.CharField(max_length=120, unique=True)
    cohort_device_number = models.CharField(max_length=120, blank=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    ce_marking = models.CharField(max_length=120, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    contact_data = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.serial_number})"


class CategoryDocument(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to="category_documents/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "txt", "png", "jpg"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.title


class DeviceAppointment(models.Model):
    class AppointmentType(models.TextChoices):
        CALIBRATION = "calibration", "Kalibrierung"
        MAINTENANCE = "maintenance", "Wartung"
        OTHER = "other", "Sonstiges"

    medical_device = models.ForeignKey(MedicalDevice, on_delete=models.CASCADE, related_name="appointments")
    appointment_type = models.CharField(max_length=30, choices=AppointmentType.choices, default=AppointmentType.MAINTENANCE)
    due_date = models.DateField()
    note = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self) -> str:
        return f"{self.get_appointment_type_display()} - {self.medical_device.name}"

    @property
    def days_until_due(self) -> int:
        from django.utils import timezone

        return (self.due_date - timezone.localdate()).days
