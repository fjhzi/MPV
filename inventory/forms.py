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
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class DeviceAppointmentForm(forms.ModelForm):
    class Meta:
        model = DeviceAppointment
        fields = ["appointment_type", "due_date", "note"]
        widgets = {
            "due_date": DateInput(),
            "note": forms.Textarea(attrs={"rows": 2}),
        }


class CategoryDocumentForm(forms.ModelForm):
    class Meta:
        model = CategoryDocument
        fields = ["category", "title", "file"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
