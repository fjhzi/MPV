from django.db import migrations


DEFAULT_CATEGORY_NAMES = [
    "AGE-Reader",
    "Actigraph",
    "Blutdruckmessgerät",
    "Defibrillator",
    "Druckalgometer",
    "EKG",
    "Fahrradergometer",
    "Feno",
    "Funduskamera",
    "Gefrierschrank",
    "Gefäßanalyse",
    "Greifkraftmessgerät",
    "Kalibrierungspumpe",
    "Kühlschrank",
    "Sauganlage",
    "Schwenkmischer",
    "Somnowatch",
    "Sonstiges",
    "Spirometrie",
    "Stadiometer",
    "Ultraschallsystem",
    "Waage",
    "Zentrifuge",
]


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    for name in DEFAULT_CATEGORY_NAMES:
        Category.objects.get_or_create(name=name)


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    Category.objects.filter(name__in=DEFAULT_CATEGORY_NAMES, devices__isnull=True, documents__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_remove_medicaldevice_ce_marking_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
