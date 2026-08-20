import datetime
from datetime import date, timedelta, datetime

from django.core.exceptions import PermissionDenied
from django.utils.dateparse import parse_date
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

from django.http import HttpResponseRedirect
from django.db import DatabaseError
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import CategoryDocumentForm, CategoryForm, DeviceAppointmentForm, MedicalDeviceForm, RoomForm
from .models import Category, CategoryDocument, DeviceAppointment,  MedicalDevice, Room, DeviceAuditLog
from .services.backup import create_export_file, restore_backup_data
import json
from django.core.serializers.json import DjangoJSONEncoder

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
        
        # KPI Metrics for Dashboard
        today = timezone.localdate()
        allowed_reminder_types = [
            "calibration",
            "maintenance_mtk",
            "maintenance_stk",
            "maintenance_dguv3"
        ]
        context["total_devices_count"] = MedicalDevice.objects.count()
        context["active_devices_count"] = MedicalDevice.objects.filter(activity_status=MedicalDevice.ActivityStatus.ACTIVE).count()
        context["defective_devices_count"] = MedicalDevice.objects.filter(functional_status=MedicalDevice.FunctionalStatus.DEFECTIVE).count()
        context["overdue_appointments_count"] = DeviceAppointment.objects.filter(completed=False, appointment_type__in=allowed_reminder_types, due_date__lt=today).count()
        context["due_soon_appointments_count"] = DeviceAppointment.objects.filter(completed=False, appointment_type__in=allowed_reminder_types, due_date__gte=today, due_date__lte=today + timedelta(days=30)).count()

        # 🚨 HIER DIE ZWEITE ÄNDERUNG: aktuellen Status für das Template übergeben
        context["activity_status"] = self.request.GET.get("activity_status", "active").strip()
        
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

    def form_valid(self, form):
        response = super().form_valid(form)
        DeviceAuditLog.objects.create(
            medical_device=self.object,
            action="Gerät erstellt",
            description=f"Gerät '{self.object.name}' (SN: {self.object.serial_number}) wurde angelegt."
        )
        return response


class MedicalDeviceUpdateView(UpdateView):
    model = MedicalDevice
    form_class = MedicalDeviceForm
    template_name = "inventory/form.html"

    def get_success_url(self):
        return reverse_lazy("device-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        old_instance = MedicalDevice.objects.get(pk=self.get_object().pk)
        response = super().form_valid(form)
        
        field_labels = {
            "name": "Name des Geräts",
            "category": "Kategorie",
            "room": "Raum",
            "activity_status": "Aktivitätsstatus",
            "functional_status": "Funktionsstatus",
            "serial_number": "Seriennummer",
            "cohort_device_number": "Gerätenummer (Kohorte)",
            "manufacturer": "Hersteller",
            "delivery_date": "Lieferdatum",
            "contact_data": "Kontaktdaten",
            "notes": "Anmerkungen",
        }
        changes = []
        for field, label in field_labels.items():
            old_val = getattr(old_instance, field)
            new_val = getattr(self.object, field)
            
            if field == "category":
                old_str = str(old_val) if old_val else "-"
                new_str = str(new_val) if new_val else "-"
            elif field == "room":
                old_str = old_val.name if old_val else "-"
                new_str = new_val.name if new_val else "-"
            elif field == "activity_status":
                old_str = old_instance.get_activity_status_display()
                new_str = self.object.get_activity_status_display()
            elif field == "functional_status":
                old_str = old_instance.get_functional_status_display()
                new_str = self.object.get_functional_status_display()
            elif field == "delivery_date":
                old_str = old_val.strftime('%d.%m.%Y') if old_val else "-"
                new_str = new_val.strftime('%d.%m.%Y') if new_val else "-"
            else:
                old_str = str(old_val) if old_val else "-"
                new_str = str(new_val) if new_val else "-"
                
            if old_val != new_val:
                changes.append(f"{label}: '{old_str}' → '{new_str}'")
                
        if changes:
            desc = "Änderungen: " + ", ".join(changes)
        else:
            desc = f"Stammdaten von '{self.object.name}' wurden aktualisiert."
            
        DeviceAuditLog.objects.create(
            medical_device=self.object,
            action="Gerät bearbeitet",
            description=desc
        )
        return response


class MedicalDeviceDeleteView(DeleteView):
    model = MedicalDevice
    template_name = "inventory/confirm_delete.html"
    success_url = reverse_lazy("dashboard")

from django.views.generic import DetailView
from django.db import DatabaseError
# ... (deine anderen Imports wie MedicalDevice, DeviceAppointmentForm)

class MedicalDeviceDetailView(DetailView):
    model = MedicalDevice
    template_name = "inventory/device_detail.html"
    context_object_name = "device"

    def _safe_related_list(self, queryset, *, missing_table_context_key, context):
        try:
            return list(queryset.all())
        except DatabaseError:
            context[missing_table_context_key] = True
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. ALLE Termine abrufen, absteigend sortiert (Zukünftige/Neueste oben, Alte unten)
        # Wir sortieren standardmäßig nach due_date
        all_qs = self.object.appointments.all().order_by('-due_date')
        
        context["appointments"] = self._safe_related_list(
            all_qs,
            missing_table_context_key="appointments_unavailable",
            context=context,
        )

        context["audit_logs"] = self._safe_related_list(
            self.object.audit_logs.all(),
            missing_table_context_key="audit_logs_unavailable",
            context=context,
        )
        
        # 2. Context befüllen (history_items fällt komplett weg!)
        context["appointment_form"] = DeviceAppointmentForm()
        
        # 🚨 HIER IST DIE MAGIE: 
        # Wir nehmen alle Dokumente der Kategorie, aber filtern sie so, 
        # dass nur die ohne spezifisches Gerät (isnull=True) 
        # ODER die für genau dieses Gerät (device=self.object) übrig bleiben!
        context["category_documents"] = self.object.category.documents.filter(
            Q(device__isnull=True) | Q(device=self.object)
        ).order_by('-document_date')

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
                old_name = category.name
                old_dguv3 = category.dguv3_interval_months
                old_mtk = category.mtk_interval_months
                old_stk = category.stk_interval_months
                old_cal = category.calibration_interval_months

                form = CategoryForm(request.POST, instance=category, prefix=f"category_{category.pk}")
                if form.is_valid():
                    updated_cat = form.save()
                    messages.success(request, "Kategorie erfolgreich aktualisiert.")

                    cat_changes = []
                    if old_name != updated_cat.name:
                        cat_changes.append(f"Name: '{old_name}' → '{updated_cat.name}'")
                    if old_dguv3 != updated_cat.dguv3_interval_months:
                        cat_changes.append(f"DGUV3-Intervall: {old_dguv3 or '-'} → {updated_cat.dguv3_interval_months or '-'} Monate")
                    if old_mtk != updated_cat.mtk_interval_months:
                        cat_changes.append(f"MTK-Intervall: {old_mtk or '-'} → {updated_cat.mtk_interval_months or '-'} Monate")
                    if old_stk != updated_cat.stk_interval_months:
                        cat_changes.append(f"STK-Intervall: {old_stk or '-'} → {updated_cat.stk_interval_months or '-'} Monate")
                    if old_cal != updated_cat.calibration_interval_months:
                        cat_changes.append(f"Kalibrierungsintervall: {old_cal or '-'} → {updated_cat.calibration_interval_months or '-'} Monate")

                    if cat_changes:
                        desc = f"Kategorie-Stammdaten aktualisiert: " + ", ".join(cat_changes)
                        for dev in updated_cat.devices.all():
                            DeviceAuditLog.objects.create(
                                medical_device=dev,
                                action="Kategorie-Stammdaten geändert",
                                description=desc
                            )
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
        
        # Formular nur initialisieren, wenn es nicht schon durch einen Fehler im POST-Request übergeben wurde
        if "document_form" not in context:
            context["document_form"] = CategoryDocumentForm()
            
        try:
            context["categories"] = Category.objects.only("id", "name").prefetch_related("documents")
            context["categories_schema_unavailable"] = False
        except DatabaseError:
            context["categories"] = []
            context["categories_schema_unavailable"] = True

        # NEU: Geräte laden (jetzt inkl. Seriennummer!)
        devices = MedicalDevice.objects.only('id', 'name', 'serial_number', 'category_id')
        devices_map = {}
        for dev in devices:
            cat_id = str(dev.category_id)
            if cat_id not in devices_map:
                devices_map[cat_id] = []
            
            # Wir zeigen die Seriennummer an. Falls diese bei einem Gerät mal leer sein sollte, 
            # nutzen wir als Fallback den normalen Namen.
            # (Alternativ könntest du auch f"{dev.serial_number} - {dev.name}" nutzen)
            display_name = dev.serial_number if dev.serial_number else dev.name
            
            devices_map[cat_id].append({'id': dev.id, 'name': display_name})
            
        context['devices_by_category_json'] = json.dumps(devices_map, cls=DjangoJSONEncoder)

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "upload_document":
            form = CategoryDocumentForm(request.POST, request.FILES)
            if form.is_valid():
                # commit=False speichert das Objekt noch nicht in der DB, 
                # gibt uns aber die Instanz zum Überprüfen
                document = form.save(commit=False)
                
                # 🚨 SECURITY CHECK (Fehlersicherheit)
                # Jemand könnte im Frontend per Dev-Tools ein Gerät einer falschen Kategorie unterschieben.
                if document.device and document.device.category != document.category:
                    messages.error(request, "Sicherheitsverletzung: Das gewählte Gerät gehört nicht zur angegebenen Kategorie.")
                    # Seite neu laden und das Formular MIT den Fehlern anzeigen
                    return self.render_to_response(self.get_context_data(document_form=form))
                
                # Wenn alles passt: Speichern!
                document.save()
                if document.device:
                    DeviceAuditLog.objects.create(
                        medical_device=document.device,
                        action="Dokument hinzugefügt",
                        description=f"Dokument '{document.title}' wurde hinzugefügt."
                    )
                else:
                    for dev in document.category.devices.all():
                        DeviceAuditLog.objects.create(
                            medical_device=dev,
                            action="Dokument hinzugefügt",
                            description=f"Kategoriendokument '{document.title}' (Kategorie: {document.category.name}) wurde hinzugefügt."
                        )
                messages.success(request, "Dokument erfolgreich hochgeladen.")
            else:
                # Standard-Formularfehler (z.B. falsches Dateiformat) abfangen
                messages.error(request, "Bitte korrigiere die Fehler im Formular.")
                return self.render_to_response(self.get_context_data(document_form=form))
                
        elif action == "delete_document":
                document = get_object_or_404(CategoryDocument, pk=request.POST.get("document_id"))
                doc_title = document.title
                device = document.device
                category = document.category
                document.delete()

                if device:
                    DeviceAuditLog.objects.create(
                        medical_device=device,
                        action="Dokument gelöscht",
                        description=f"Dokument '{doc_title}' wurde gelöscht."
                    )
                else:
                    for dev in category.devices.all():
                        DeviceAuditLog.objects.create(
                            medical_device=dev,
                            action="Dokument gelöscht",
                            description=f"Kategoriendokument '{doc_title}' wurde gelöscht."
                        )
                messages.success(request, "Dokument erfolgreich gelöscht.")
                # Leitet zurück zur Ursprungsseite
                return redirect(request.POST.get("next", request.path_info))

        elif action == "edit_document":
            document = get_object_or_404(CategoryDocument, pk=request.POST.get("document_id"))
            old_title = document.title
            new_title = request.POST.get("title")
            new_date = request.POST.get("document_date")
            
            if new_title:
                document.title = new_title
            if new_date:
                document.document_date = new_date
                
            document.save()

            desc = f"Dokument '{old_title}' wurde bearbeitet (neuer Titel: '{document.title}')."
            if document.device:
                DeviceAuditLog.objects.create(
                    medical_device=document.device,
                    action="Dokument bearbeitet",
                    description=desc
                )
            else:
                for dev in document.category.devices.all():
                    DeviceAuditLog.objects.create(
                        medical_device=dev,
                        action="Dokument bearbeitet",
                        description=desc
                    )
            messages.success(request, "Dokument erfolgreich aktualisiert.")
            return redirect(request.POST.get("next", request.path_info))
            
        # Post/Redirect/Get-Pattern: Verhindert, dass beim Neuladen der Seite (F5) 
        # das Formular erneut abgeschickt wird. (Alternativ kannst du auch bei deinem self.get() bleiben)
        return redirect(request.path_info)


class AppointmentCreateView(CreateView):
    model = DeviceAppointment
    form_class = DeviceAppointmentForm

    def form_valid(self, form):
        form.instance.medical_device_id = self.kwargs["pk"]
        response = super().form_valid(form)
        DeviceAuditLog.objects.create(
            medical_device=self.object.medical_device,
            action="Termin erstellt",
            description=f"Termin '{self.object.get_appointment_type_display()}' (Fällig: {self.object.due_date}) wurde erstellt."
        )
        return response

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
        # Basis-QuerySet mit Joins[cite: 1]
        queryset = DeviceAppointment.objects.select_related("medical_device", "medical_device__category", "medical_device__room")
        date_filter = self.request.GET.get("date_filter", "all_open")
        today = timezone.localdate()

       # Liste der relevanten Terminarten für den Reminder
        allowed_categories = [
            "calibration",
            "maintenance_mtk",
            "maintenance_stk",
            "maintenance_dguv3"
        ]

        # Hier auf appointment_type ändern
        queryset = queryset.filter(
            completed=False,
            appointment_type__in=allowed_categories
        )

        # Datumsfilter anwenden[cite: 1]
        if date_filter == "overdue":
            queryset = queryset.filter(due_date__lt=today)
        elif date_filter == "next_7":
            queryset = queryset.filter(due_date__gte=today, due_date__lte=today + timedelta(days=7))
        elif date_filter == "next_30":
            queryset = queryset.filter(due_date__gte=today, due_date__lte=today + timedelta(days=30))
            
        return queryset.order_by("due_date", "medical_device")


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
        app_type = appointment.get_appointment_type_display()
        due_date = appointment.due_date
        device = appointment.medical_device
        appointment.delete()
        DeviceAuditLog.objects.create(
            medical_device=device,
            action="Termin gelöscht",
            description=f"Termin '{app_type}' (Fällig: {due_date}) wurde gelöscht."
        )
        return HttpResponseRedirect(reverse_lazy("device-detail", kwargs={"pk": device_pk}))


class AppointmentToggleCompleteView(View):
    def post(self, request, device_pk, appointment_pk):
        appointment = get_object_or_404(DeviceAppointment, pk=appointment_pk, medical_device_id=device_pk)
        appointment.completed = not appointment.completed
        appointment.save(update_fields=["completed"])
        status_str = "als erledigt" if appointment.completed else "wieder als offen"
        DeviceAuditLog.objects.create(
            medical_device=appointment.medical_device,
            action="Termin-Status geändert",
            description=f"Termin '{appointment.get_appointment_type_display()}' wurde {status_str} markiert."
        )
        return HttpResponseRedirect(reverse_lazy("device-detail", kwargs={"pk": device_pk}))
    
def complete_and_reschedule(request, device_pk, appointment_pk):
    if request.method == "POST":
        current_appointment = get_object_or_404(DeviceAppointment, id=appointment_pk, medical_device_id=device_pk)
        device = current_appointment.medical_device
        
        # 1. Aktuellen Termin als erledigt markieren
        current_appointment.completed = True
        current_appointment.save()

        DeviceAuditLog.objects.create(
            medical_device=device,
            action="Termin erledigt",
            description=f"Termin '{current_appointment.get_appointment_type_display()}' (Fällig: {current_appointment.due_date}) wurde erledigt."
        )
        
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

            DeviceAuditLog.objects.create(
                medical_device=device,
                action="Folgetermin angelegt",
                description=f"Wiedervorlage für '{current_appointment.get_appointment_type_display()}' am {new_date.strftime('%d.%m.%Y')} geplant."
            )
            
            type_name = current_appointment.get_appointment_type_display()
            messages.success(request, f"Termin '{type_name}' erledigt. Folgeprüfung am {new_date.strftime('%d.%m.%Y')} angelegt.")
        else:
            type_name = current_appointment.get_appointment_type_display()
            messages.success(request, f"Termin '{type_name}' wurde als erledigt markiert.")
            
        return redirect('device-detail', pk=device.pk)
        
    return redirect('dashboard')

def sitevisit_view(request):
    """Zeigt die filterbare Liste der erledigten Termine/Wartungen an."""
    appointments = DeviceAppointment.objects.filter(completed=True).order_by('medical_device__category', 'due_date')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    # WICHTIG: getlist() holt alle markierten Checkboxen als Liste
    selected_types = request.GET.getlist('appointment_type')

    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            appointments = appointments.filter(due_date__gte=parsed_start)
    
    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            appointments = appointments.filter(due_date__lte=parsed_end)
            
    if selected_types:
        # WICHTIG: __in prüft, ob die Terminart in der Liste der ausgewählten Typen ist
        appointments = appointments.filter(appointment_type__in=selected_types)

    context = {
        'appointments': appointments,
        'start_date': start_date or '',
        'end_date': end_date or '',
        'selected_types': selected_types,  # Liste an das Template übergeben
        'type_choices': DeviceAppointment._meta.get_field('appointment_type').choices,
    }
    return render(request, 'inventory/sitevisit.html', context)


def sitevisit_print_view(request):
    """Generiert eine HTML Ansicht zum Drucken aus den gefilterten erledigten Terminen."""
    appointments = DeviceAppointment.objects.filter(completed=True).order_by('medical_device__category', 'due_date')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    # Auch hier getlist() verwenden
    selected_types = request.GET.getlist('appointment_type')

    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            appointments = appointments.filter(due_date__gte=parsed_start)
    
    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            appointments = appointments.filter(due_date__lte=parsed_end)
            
    if selected_types:
        appointments = appointments.filter(appointment_type__in=selected_types)

    # Wandelt die technischen Schlüssel in einen kommagetrennten String für den Bericht um
    selected_type_display = "Alle"
    if selected_types:
        choices_dict = dict(DeviceAppointment._meta.get_field('appointment_type').choices)
        display_names = [str(choices_dict.get(t, t)) for t in selected_types]
        selected_type_display = ", ".join(display_names)

    context = {
        'appointments': appointments,
        'start_date': parse_date(start_date) if start_date else None,
        'end_date': parse_date(end_date) if end_date else None,
        'selected_type_display': selected_type_display,
    }

    return render(request, 'inventory/sitevisit_print.html', context)


def export_backup_view(request):
    if request.method == "POST":
        include_files = request.POST.get("include_files") == "on"
        filename, content, content_type = create_export_file(include_files=include_files)
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return redirect('stammdaten')


def import_backup_view(request):
    if request.method == "POST":
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        backup_file = request.FILES.get("backup_file")
        if not backup_file:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Bitte wähle eine Backup-Datei aus."}, status=400)
            messages.error(request, "Bitte wähle eine Backup-Datei aus.")
            return redirect('stammdaten')
        
        try:
            stats = restore_backup_data(backup_file)
            msg = (
                f"Backup erfolgreich eingespielt! Wiederhergestellt: "
                f"{stats['categories']} Kategorien, {stats['rooms']} Räume, "
                f"{stats['devices']} Geräte, {stats['documents']} Dokumente, {stats['appointments']} Termine."
            )
            if is_ajax:
                return JsonResponse({
                    "status": "success",
                    "message": msg,
                    "stats": stats
                })
            messages.success(request, msg)
        except Exception as e:
            err_msg = f"Fehler beim Wiederherstellen des Backups: {str(e)}"
            if is_ajax:
                return JsonResponse({"status": "error", "message": err_msg}, status=400)
            messages.error(request, err_msg)
            
    return redirect('stammdaten')
