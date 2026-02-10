from django.urls import path

from .views import (
    AppointmentCreateView,
    CategoryListCreateView,
    DashboardView,
    MedicalDeviceCreateView,
    MedicalDeviceDeleteView,
    MedicalDeviceDetailView,
    MedicalDeviceUpdateView,
    ReminderView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("devices/new/", MedicalDeviceCreateView.as_view(), name="device-create"),
    path("devices/<int:pk>/", MedicalDeviceDetailView.as_view(), name="device-detail"),
    path("devices/<int:pk>/edit/", MedicalDeviceUpdateView.as_view(), name="device-edit"),
    path("devices/<int:pk>/delete/", MedicalDeviceDeleteView.as_view(), name="device-delete"),
    path("devices/<int:pk>/appointments/new/", AppointmentCreateView.as_view(), name="appointment-create"),
    path("stammdaten/", CategoryListCreateView.as_view(), name="stammdaten"),
    path("reminders/", ReminderView.as_view(), name="reminders"),
]
