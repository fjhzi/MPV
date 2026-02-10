from django.contrib import admin

from .models import Category, CategoryDocument, DeviceAppointment, MedicalDevice, Room


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(MedicalDevice)
class MedicalDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "serial_number", "category", "room", "activity_status", "functional_status")
    list_filter = ("category", "room", "activity_status", "functional_status")
    search_fields = ("name", "serial_number", "cohort_device_number", "manufacturer")


@admin.register(CategoryDocument)
class CategoryDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "uploaded_at")
    list_filter = ("category",)


@admin.register(DeviceAppointment)
class DeviceAppointmentAdmin(admin.ModelAdmin):
    list_display = ("medical_device", "appointment_type", "due_date", "completed")
    list_filter = ("appointment_type", "completed")
