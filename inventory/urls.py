from django.urls import path

from .views import (
    AppointmentCreateView,
    AppointmentDeleteView,
    AppointmentToggleCompleteView,
    EventCreateView,
    EventDeleteView,
    CategoryListCreateView,
    DashboardView,
    DocumentManagementView,
    MedicalDeviceCreateView,
    MedicalDeviceDeleteView,
    MedicalDeviceDetailView,
    MedicalDeviceUpdateView,
    ReminderArchiveView,
    ReminderView,
    complete_and_reschedule,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("devices/new/", MedicalDeviceCreateView.as_view(), name="device-create"),
    path("devices/<int:pk>/", MedicalDeviceDetailView.as_view(), name="device-detail"),
    path("devices/<int:pk>/edit/", MedicalDeviceUpdateView.as_view(), name="device-edit"),
    path("devices/<int:pk>/delete/", MedicalDeviceDeleteView.as_view(), name="device-delete"),
    path("devices/<int:pk>/appointments/new/", AppointmentCreateView.as_view(), name="appointment-create"),
    path("devices/<int:device_pk>/appointments/<int:appointment_pk>/delete/", AppointmentDeleteView.as_view(), name="appointment-delete"),
    path("devices/<int:device_pk>/appointments/<int:appointment_pk>/toggle-complete/", AppointmentToggleCompleteView.as_view(), name="appointment-toggle-complete"),
    path("devices/<int:pk>/events/new/", EventCreateView.as_view(), name="event-create"),
    path("devices/<int:device_pk>/events/<int:event_pk>/delete/", EventDeleteView.as_view(), name="event-delete"),
    path("stammdaten/", CategoryListCreateView.as_view(), name="stammdaten"),
    path("dokumente/", DocumentManagementView.as_view(), name="documents"),
    path("reminders/", ReminderView.as_view(), name="reminders"),
    path("reminders/archive/", ReminderArchiveView.as_view(), name="reminders-archive"),
    path('event/<int:event_id>/complete-and-reschedule/', complete_and_reschedule, name='complete_and_reschedule'),
    path('device/<int:device_pk>/appointment/<int:appointment_pk>/complete-reschedule/', complete_and_reschedule, name='appointment-complete-reschedule'),
]
