from django import forms

from .models import Category, CategoryDocument, DeviceAppointment, DeviceEvent, MedicalDevice, Room


class DateInput(forms.DateInput):
    input_type = "date"


class BootstrapStyledModelForm(forms.ModelForm):
    """Apply Bootstrap classes consistently to all form widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                base_class = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                base_class = "form-select"
            elif isinstance(widget, forms.ClearableFileInput):
                base_class = "form-control"
            else:
                base_class = "form-control"

            classes = widget.attrs.get("class", "").split()
            if base_class not in classes:
                classes.append(base_class)
            widget.attrs["class"] = " ".join(filter(None, classes))


class MedicalDeviceForm(BootstrapStyledModelForm):
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
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class DeviceAppointmentForm(BootstrapStyledModelForm):
    class Meta:
        model = DeviceAppointment
        fields = ["appointment_type", "due_date", "note"]
        widgets = {
            "due_date": DateInput(),
            "note": forms.Textarea(attrs={"rows": 2}),
        }


class DeviceEventForm(BootstrapStyledModelForm):
    class Meta:
        model = DeviceEvent
        fields = ["event_date", "note"]
        widgets = {
            "event_date": DateInput(),
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
