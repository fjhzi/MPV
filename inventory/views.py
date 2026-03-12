import datetime
from datetime import date, timedelta, datetime

from django.core.exceptions import PermissionDenied


from django.http import HttpResponseRedirect
from django.db import DatabaseError
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
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
        
        # 1. Termine laden
        context["appointment_form"] = DeviceAppointmentForm()
        appointments = self._safe_related_list(
            self.object.appointments,
            missing_table_context_key="appointments_unavailable",
            context=context,
        )
        context["appointments"] = appointments
        
        # 2. Ereignisse laden
        context["event_form"] = DeviceEventForm()
        events = self._safe_related_list(
            self.object.events,
            missing_table_context_key="events_unavailable",
            context=context,
        )
        context["events"] = events
        
        context["category_documents"] = self.object.category.documents.all()

        # --- NEU: Listen zusammenführen und sortieren ---
        history_items = []
        
        for appt in appointments:
            appt.is_appointment = True       # Markierung für HTML
            appt.sort_date = appt.due_date   # Einheitlicher Name zum Sortieren
            history_items.append(appt)
            
        for evt in events:
            evt.is_appointment = False       # Markierung für HTML
            evt.sort_date = evt.event_date   # Einheitlicher Name zum Sortieren
            history_items.append(evt)

        # Sortieren: Höchstes Datum (neueste) zuerst. Fallback auf date.min, falls leer.
        history_items.sort(key=lambda x: x.sort_date or date.min, reverse=True)
        
        # Gemischte Liste in den Context packen
        context["history_items"] = history_items

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
        
        # NEU: Räume und ihre Edit-Formulare laden
        rooms = list(Room.objects.all())
        context["rooms"] = rooms
        context["room_edit_forms"] = [
            (room, RoomForm(instance=room, prefix=f"room_{room.pk}"))
            for room in rooms
        ]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "create_category":
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Kategorie erfolgreich erstellt.")
                
        elif action == "create_room":
            form = RoomForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Raum erfolgreich erstellt.")
                
        elif action == "update_category":
            try:
                category = get_object_or_404(Category, pk=request.POST.get("category_id"))
                form = CategoryForm(request.POST, instance=category, prefix=f"category_{category.pk}")
                if form.is_valid():
                    form.save()
                    messages.success(request, "Kategorie erfolgreich aktualisiert.")
            except DatabaseError:
                pass

        # NEU: Raum aktualisieren
        elif action == "update_room":
            try:
                room = get_object_or_404(Room, pk=request.POST.get("room_id"))
                form = RoomForm(request.POST, instance=room, prefix=f"room_{room.pk}")
                if form.is_valid():
                    form.save()
                    messages.success(request, "Raum erfolgreich aktualisiert.")
            except DatabaseError:
                pass

        elif action == "delete_category":
            if not request.user.is_staff:
                raise PermissionDenied
            category = get_object_or_404(Category, pk=request.POST.get("category_id"))
            
            # BOMBENSICHERE METHODE: Direkt über das MedicalDevice Model filtern
            if MedicalDevice.objects.filter(category=category).exists():
                messages.error(request, f"Die Kategorie '{category.name}' kann nicht gelöscht werden, da sie noch Geräten zugewiesen ist.")
            else:
                try:
                    category.delete()
                    messages.success(request, "Kategorie erfolgreich gelöscht.")
                except ProtectedError:
                    messages.error(request, "Die Kategorie ist geschützt und kann nicht gelöscht werden.")
                    
        elif action == "delete_room":
            if not request.user.is_staff:
                raise PermissionDenied
            room = get_object_or_404(Room, pk=request.POST.get("room_id"))
            
            # BOMBENSICHERE METHODE: Direkt über das MedicalDevice Model filtern
            if MedicalDevice.objects.filter(room=room).exists():
                messages.error(request, f"Der Raum '{room.name}' kann nicht gelöscht werden, da er noch Geräten zugewiesen ist.")
            else:
                try:
                    room.delete()
                    messages.success(request, "Raum erfolgreich gelöscht.")
                except ProtectedError:
                    messages.error(request, "Der Raum ist geschützt und kann nicht gelöscht werden.")
                    
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

def complete_and_reschedule(request, device_pk, appointment_pk):
    if request.method == "POST":
        current_appointment = get_object_or_404(DeviceAppointment, id=appointment_pk, medical_device_id=device_pk)
        device = current_appointment.medical_device
        
        # 1. Aktuellen Termin als erledigt markieren
        current_appointment.completed = True
        current_appointment.save()
        
        # 2. Prüfen, ob eine Wiedervorlage gewünscht ist
        create_followup = request.POST.get("create_followup") == "true"
        
        if create_followup:
            # 3. Das genaue Datum aus dem Datepicker holen
            date_str = request.POST.get("next_interval_date")
            
            try:
                # String "YYYY-MM-DD" in ein Python-Datum umwandeln
                new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                # Fallback: Falls das Datum leer ist oder fehlerhaft übertragen wurde
                new_date = timezone.now().date() + timedelta(days=365)
                
            # Neuen Termin mit dem exakten Datum anlegen
            DeviceAppointment.objects.create(
                medical_device=device,
                appointment_type=current_appointment.appointment_type,
                due_date=new_date,
                completed=False
            )
            
            type_name = current_appointment.get_appointment_type_display()
            messages.success(request, f"Termin '{type_name}' erledigt. Folgeprüfung am {new_date.strftime('%d.%m.%Y')} angelegt.")
        else:
            type_name = current_appointment.get_appointment_type_display()
            messages.success(request, f"Termin '{type_name}' wurde als erledigt markiert.")
            
        return redirect('device-detail', pk=device.pk)
        
    return redirect('dashboard')