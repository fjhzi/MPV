import datetime

from django.core.exceptions import PermissionDenied

from django.http import HttpResponseRedirect
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import CategoryDocumentForm, CategoryForm, DeviceAppointmentForm, MedicalDeviceForm, RoomForm
from .models import Category, DeviceAppointment, MedicalDevice, Room


class DashboardView(ListView):
    model = MedicalDevice
    template_name = "inventory/dashboard.html"
    context_object_name = "devices"
    paginate_by = 20

    allowed_sort_fields = {
        "name": "name",
        "category": "category__name",
        "room": "room__name",
        "status": "activity_status",
        "condition": "functional_status",
        "delivery_date": "delivery_date",
    }

    def get_queryset(self):
        queryset = (
            MedicalDevice.objects.select_related("category", "room")
            .all()
        )

        search = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        room = self.request.GET.get("room", "").strip()
        activity_status = self.request.GET.get("activity_status", "").strip()
        functional_status = self.request.GET.get("functional_status", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(cohort_device_number__icontains=search)
                | Q(manufacturer__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if room:
            queryset = queryset.filter(room_id=room)
        if activity_status:
            queryset = queryset.filter(activity_status=activity_status)
        if functional_status:
            queryset = queryset.filter(functional_status=functional_status)

        sort = self.request.GET.get("sort", "name")
        direction = self.request.GET.get("direction", "asc")
        sort_field = self.allowed_sort_fields.get(sort, "name")
        if direction == "desc":
            sort_field = f"-{sort_field}"

        return queryset.order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["rooms"] = Room.objects.all()
        context["sort"] = self.request.GET.get("sort", "name")
        context["direction"] = self.request.GET.get("direction", "asc")
        context["next_direction"] = "desc" if context["direction"] == "asc" else "asc"
        return context


class MedicalDeviceCreateView(CreateView):
    model = MedicalDevice
    form_class = MedicalDeviceForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("dashboard")


class MedicalDeviceUpdateView(UpdateView):
    model = MedicalDevice
    form_class = MedicalDeviceForm
    template_name = "inventory/form.html"

    def get_success_url(self):
        return reverse_lazy("device-detail", kwargs={"pk": self.object.pk})


class MedicalDeviceDeleteView(DeleteView):
    model = MedicalDevice
    template_name = "inventory/confirm_delete.html"
    success_url = reverse_lazy("dashboard")


class MedicalDeviceDetailView(DetailView):
    model = MedicalDevice
    template_name = "inventory/device_detail.html"
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appointment_form"] = DeviceAppointmentForm()
        context["appointments"] = self.object.appointments.all()
        context["category_documents"] = self.object.category.documents.all()
        return context


class CategoryListCreateView(TemplateView):
    template_name = "inventory/stammdaten.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category_form"] = CategoryForm()
        context["room_form"] = RoomForm()
        context["document_form"] = CategoryDocumentForm()
        context["categories"] = Category.objects.prefetch_related("documents")
        context["rooms"] = Room.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_category":
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
        elif action == "create_room":
            form = RoomForm(request.POST)
            if form.is_valid():
                form.save()
        elif action == "delete_category":
            if not request.user.is_staff:
                raise PermissionDenied
            category = get_object_or_404(Category, pk=request.POST.get("category_id"))
            try:
                category.delete()
            except ProtectedError:
                pass
        elif action == "delete_room":
            if not request.user.is_staff:
                raise PermissionDenied
            room = get_object_or_404(Room, pk=request.POST.get("room_id"))
            room.delete()
        elif action == "upload_document":
            form = CategoryDocumentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
        return self.get(request, *args, **kwargs)


class AppointmentCreateView(CreateView):
    model = DeviceAppointment
    form_class = DeviceAppointmentForm

    def form_valid(self, form):
        form.instance.medical_device_id = self.kwargs["pk"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("device-detail", kwargs={"pk": self.kwargs["pk"]})


class AppointmentDeleteView(DeleteView):
    model = DeviceAppointment
    template_name = "inventory/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("device-detail", kwargs={"pk": self.object.medical_device_id})


class ReminderView(ListView):
    model = DeviceAppointment
    template_name = "inventory/reminders.html"
    context_object_name = "appointments"

    def get_queryset(self):
        queryset = DeviceAppointment.objects.select_related("medical_device", "medical_device__category", "medical_device__room")
        date_filter = self.request.GET.get("date_filter", "all_open")
        today = timezone.localdate()

        queryset = queryset.filter(completed=False)

        if date_filter == "overdue":
            queryset = queryset.filter(due_date__lt=today)
        elif date_filter == "next_7":
            queryset = queryset.filter(due_date__gte=today, due_date__lte=today + datetime.timedelta(days=7))
        elif date_filter == "next_30":
            queryset = queryset.filter(due_date__gte=today, due_date__lte=today + datetime.timedelta(days=30))
        return queryset.order_by("due_date")


class ReminderArchiveView(ListView):
    model = DeviceAppointment
    template_name = "inventory/reminders_archive.html"
    context_object_name = "appointments"

    def get_queryset(self):
        return (
            DeviceAppointment.objects.select_related("medical_device", "medical_device__category", "medical_device__room")
            .filter(completed=True)
            .order_by("-due_date")
        )


class AppointmentDeleteView(View):
    def post(self, request, device_pk, appointment_pk):
        appointment = get_object_or_404(DeviceAppointment, pk=appointment_pk, medical_device_id=device_pk)
        appointment.delete()
        return HttpResponseRedirect(reverse_lazy("device-detail", kwargs={"pk": device_pk}))


class AppointmentToggleCompleteView(View):
    def post(self, request, device_pk, appointment_pk):
        appointment = get_object_or_404(DeviceAppointment, pk=appointment_pk, medical_device_id=device_pk)
        appointment.completed = not appointment.completed
        appointment.save(update_fields=["completed"])
        return HttpResponseRedirect(reverse_lazy("device-detail", kwargs={"pk": device_pk}))
