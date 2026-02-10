# Generated manually for initial prototype
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MedicalDevice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180)),
                (
                    "activity_status",
                    models.CharField(
                        choices=[("active", "Aktiv"), ("inactive", "Nicht aktiv")],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "functional_status",
                    models.CharField(
                        choices=[("functional", "Funktionsfähig"), ("defective", "Defekt")],
                        default="functional",
                        max_length=20,
                    ),
                ),
                ("serial_number", models.CharField(max_length=120, unique=True)),
                ("cohort_device_number", models.CharField(blank=True, max_length=120)),
                ("manufacturer", models.CharField(blank=True, max_length=120)),
                ("ce_marking", models.CharField(blank=True, max_length=120)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                ("contact_data", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="inventory.category"),
                ),
                (
                    "room",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devices", to="inventory.room"),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="DeviceAppointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "appointment_type",
                    models.CharField(
                        choices=[("calibration", "Kalibrierung"), ("maintenance", "Wartung"), ("other", "Sonstiges")],
                        default="maintenance",
                        max_length=30,
                    ),
                ),
                ("due_date", models.DateField()),
                ("note", models.TextField(blank=True)),
                ("completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "medical_device",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to="inventory.medicaldevice"),
                ),
            ],
            options={"ordering": ["due_date"]},
        ),
        migrations.CreateModel(
            name="CategoryDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                (
                    "file",
                    models.FileField(
                        upload_to="category_documents/",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["pdf", "doc", "docx", "txt", "png", "jpg"]
                            )
                        ],
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="inventory.category"),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
