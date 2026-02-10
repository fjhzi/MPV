from django import forms

from .models import Category, CategoryDocument, DeviceAppointment, MedicalDevice, Room


class DateInput(forms.DateInput):
    input_type = "date"


class MedicalDeviceForm(forms.ModelForm):
    class Meta:
        model = MedicalDevice
        fields = [
            "name",
            "category",
            "room",
            "activity_status",
            "functional_status",
            "serial_number",
            "cohort_device_number",
            "manufacturer",
            "ce_marking",
            "delivery_date",
            "contact_data",
            "notes",
        ]
        widgets = {
            "delivery_date": DateInput(),
            "contact_data": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name", "description"]


class DeviceAppointmentForm(forms.ModelForm):
    class Meta:
        model = DeviceAppointment
        fields = ["appointment_type", "due_date", "note", "completed"]
        widgets = {
            "due_date": DateInput(),
            "note": forms.Textarea(attrs={"rows": 2}),
        }


class CategoryDocumentForm(forms.ModelForm):
    class Meta:
        model = CategoryDocument
        fields = ["category", "title", "file"]
