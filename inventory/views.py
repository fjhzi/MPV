import datetime

from django.core.exceptions import PermissionDenied

from django.http import HttpResponseRedirect
from django.db import DatabaseError
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import CategoryDocumentForm, CategoryForm, DeviceAppointmentForm, DeviceEventForm, MedicalDeviceForm, RoomForm
from .models import Category, CategoryDocument, DeviceAppointment, DeviceEvent, MedicalDevice, Room


def _safe_category_context(*, include_edit_forms=False):
    """Return category context even when optional category columns are not migrated yet."""
    context = {"categories_schema_unavailable": False}
    try:
        categories = list(Category.objects.all())
    except DatabaseError:
        context["categories_schema_unavailable"] = True
        categories = list(Category.objects.only("id", "name"))

    context["categories"] = categories
    if include_edit_forms:
        if context["categories_schema_unavailable"]:
            context["category_edit_forms"] = [(category, None) for category in categories]
        else:
            context["category_edit_forms"] = [
                (category, CategoryForm(instance=category, prefix=f"category_{category.pk}"))
                for category in categories
            ]
    else:
        context["category_edit_forms"] = []
    return context


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
            normalized_search = search.casefold()
            activity_status_aliases = {
                "aktiv": "active",
                "active": "active",
                "nicht aktiv": "inactive",
                "inaktiv": "inactive",
                "inactive": "inactive",
            }
            functional_status_aliases = {
                "funktionsfähig": "functional",
                "funktionsfaehig": "functional",
                "functional": "functional",
                "defekt": "defective",
                "defective": "defective",
            }

            search_query = (
                Q(name__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(cohort_device_number__icontains=search)
                | Q(manufacturer__icontains=search)
                | Q(category__name__icontains=search)
                | Q(room__name__icontains=search)
                | Q(activity_status__icontains=search)
                | Q(functional_status__icontains=search)
            )

            mapped_activity_status = activity_status_aliases.get(normalized_search)
            if mapped_activity_status:
                search_query |= Q(activity_status=mapped_activity_status)

            mapped_functional_status = functional_status_aliases.get(normalized_search)
            if mapped_functional_status:
                search_query |= Q(functional_status=mapped_functional_status)

            queryset = queryset.filter(search_query)
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
        category_context = _safe_category_context()
        context["categories"] = category_context["categories"]
        context["categories_schema_unavailable"] = category_context["categories_schema_unavailable"]
        context["rooms"] = Room.objects.all()
        context["sort"] = self.request.GET.get("sort", "name")
        context["direction"] = self.request.GET.get("direction", "asc")
        context["next_direction"] = "desc" if context["direction"] == "asc" else "asc"

        base_query_params = self.request.GET.copy()
        base_query_params.pop("page", None)
        context["querystring_without_page"] = base_query_params.urlencode()

        sort_links = {}
        for sort_key in self.allowed_sort_fields:
            sort_query_params = base_query_params.copy()
            next_direction = "asc"
            if context["sort"] == sort_key and context["direction"] == "asc":
                next_direction = "desc"
            sort_query_params["sort"] = sort_key
            sort_query_params["direction"] = next_direction
            sort_links[sort_key] = sort_query_params.urlencode()
        context["sort_links"] = sort_links
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

    def _safe_related_list(self, manager, *, missing_table_context_key, context):
        try:
            return list(manager.all())
        except DatabaseError:
            context[missing_table_context_key] = True
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appointment_form"] = DeviceAppointmentForm()
        context["appointments"] = self._safe_related_list(
            self.object.appointments,
            missing_table_context_key="appointments_unavailable",
            context=context,
        )
        context["event_form"] = DeviceEventForm()
        context["events"] = self._safe_related_list(
            self.object.events,
            missing_table_context_key="events_unavailable",
            context=context,
        )
        context["category_documents"] = self.object.category.documents.all()
        return context


class CategoryListCreateView(TemplateView):
    template_name = "inventory/stammdaten.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category_form"] = CategoryForm()
        context["room_form"] = RoomForm()
        category_context = _safe_category_context(include_edit_forms=True)
        context["categories"] = category_context["categories"]
        context["category_edit_forms"] = category_context["category_edit_forms"]
        context["categories_schema_unavailable"] = category_context["categories_schema_unavailable"]
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
        elif action == "update_category":
            try:
                category = get_object_or_404(Category, pk=request.POST.get("category_id"))
                form = CategoryForm(request.POST, instance=category, prefix=f"category_{category.pk}")
                if form.is_valid():
                    form.save()
            except DatabaseError:
                pass
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
        return self.get(request, *args, **kwargs)


class DocumentManagementView(TemplateView):
    template_name = "inventory/documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document_form"] = CategoryDocumentForm()
        try:
            context["categories"] = Category.objects.only("id", "name").prefetch_related("documents")
            context["categories_schema_unavailable"] = False
        except DatabaseError:
            context["categories"] = []
            context["categories_schema_unavailable"] = True
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "upload_document":
            form = CategoryDocumentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
        elif action == "delete_document":
            document = get_object_or_404(CategoryDocument, pk=request.POST.get("document_id"))
            document.delete()
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


class EventCreateView(CreateView):
    model = DeviceEvent
    form_class = DeviceEventForm

    def form_valid(self, form):
        form.instance.medical_device_id = self.kwargs["pk"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("device-detail", kwargs={"pk": self.kwargs["pk"]})


class EventDeleteView(View):
    def post(self, request, device_pk, event_pk):
        event = get_object_or_404(DeviceEvent, pk=event_pk, medical_device_id=device_pk)
        event.delete()
        return HttpResponseRedirect(reverse_lazy("device-detail", kwargs={"pk": device_pk}))
