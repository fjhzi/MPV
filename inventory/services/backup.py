import io
import json
import os
import zipfile
from datetime import date, datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from inventory.models import Category, Room, MedicalDevice, CategoryDocument, DeviceAppointment, DeviceAuditLog


class BackupEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def generate_backup_json() -> dict:
    categories = list(Category.objects.values(
        'id', 'name', 'description', 
        'dguv3_interval_months', 'mtk_interval_months', 
        'stk_interval_months', 'calibration_interval_months'
    ))
    
    rooms = list(Room.objects.values('id', 'name', 'description'))
    
    devices = list(MedicalDevice.objects.values(
        'id', 'name', 'category_id', 'room_id',
        'activity_status', 'functional_status',
        'serial_number', 'cohort_device_number',
        'manufacturer', 'delivery_date', 'contact_data', 'notes',
        'created_at', 'updated_at'
    ))
    
    documents = list(CategoryDocument.objects.values(
        'id', 'category_id', 'device_id', 'title',
        'document_date', 'file', 'uploaded_at'
    ))
    
    appointments = list(DeviceAppointment.objects.values(
        'id', 'medical_device_id', 'appointment_type',
        'due_date', 'performed_date', 'note', 'completed', 'created_at'
    ))

    audit_logs = list(DeviceAuditLog.objects.values(
        'id', 'medical_device_id', 'action', 'description', 'created_at'
    ))

    return {
        "version": "1.0",
        "exported_at": timezone.now().isoformat(),
        "categories": categories,
        "rooms": rooms,
        "medical_devices": devices,
        "category_documents": documents,
        "device_appointments": appointments,
        "device_audit_logs": audit_logs,
    }


def create_export_file(include_files=False):
    data = generate_backup_json()
    json_bytes = json.dumps(data, cls=BackupEncoder, indent=2, ensure_ascii=False).encode('utf-8')
    
    if not include_files:
        filename = f"mpv_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        return filename, json_bytes, "application/json"
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('backup.json', json_bytes)
        
        for doc in data['category_documents']:
            file_rel_path = doc.get('file')
            if file_rel_path:
                full_path = os.path.join(settings.MEDIA_ROOT, file_rel_path)
                if os.path.isfile(full_path):
                    arcname = os.path.join('media', file_rel_path)
                    zf.write(full_path, arcname=arcname)

    buffer.seek(0)
    filename = f"mpv_backup_full_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return filename, buffer.getvalue(), "application/zip"


@transaction.atomic
def restore_backup_data(uploaded_file):
    filename = uploaded_file.name.lower()
    json_data = None

    if filename.endswith('.zip'):
        with zipfile.ZipFile(uploaded_file, 'r') as zf:
            if 'backup.json' not in zf.namelist():
                raise ValueError("Die ZIP-Datei enthält keine 'backup.json'.")
            
            json_bytes = zf.read('backup.json')
            json_data = json.loads(json_bytes.decode('utf-8'))
            
            for item in zf.namelist():
                if item.startswith('media/') and not item.endswith('/'):
                    rel_path = item[len('media/'):]
                    target_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(item) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
    else:
        content = uploaded_file.read().decode('utf-8')
        json_data = json.loads(content)

    if not isinstance(json_data, dict) or "categories" not in json_data or "medical_devices" not in json_data:
        raise ValueError("Ungültiges Backup-Format. Erforderliche Daten fehlen.")

    # Delete existing data
    DeviceAuditLog.objects.all().delete()
    DeviceAppointment.objects.all().delete()
    CategoryDocument.objects.all().delete()
    MedicalDevice.objects.all().delete()
    Room.objects.all().delete()
    Category.objects.all().delete()

    category_map = {}
    for cat_dict in json_data.get("categories", []):
        if not isinstance(cat_dict, dict) or 'name' not in cat_dict:
            raise ValueError("Ungültiges Backup: Eine Kategorie hat keinen Namen ('name' fehlt).")
        old_id = cat_dict.get('id')
        cat = Category.objects.create(
            name=cat_dict['name'],
            description=cat_dict.get('description', ''),
            dguv3_interval_months=cat_dict.get('dguv3_interval_months'),
            mtk_interval_months=cat_dict.get('mtk_interval_months'),
            stk_interval_months=cat_dict.get('stk_interval_months'),
            calibration_interval_months=cat_dict.get('calibration_interval_months'),
        )
        category_map[old_id] = cat

    room_map = {}
    for room_dict in json_data.get("rooms", []):
        if not isinstance(room_dict, dict) or 'name' not in room_dict:
            raise ValueError("Ungültiges Backup: Ein Raum hat keinen Namen ('name' fehlt).")
        old_id = room_dict.get('id')
        room = Room.objects.create(
            name=room_dict['name'],
            description=room_dict.get('description', ''),
        )
        room_map[old_id] = room

    device_map = {}
    for dev_dict in json_data.get("medical_devices", []):
        if not isinstance(dev_dict, dict) or 'name' not in dev_dict or 'serial_number' not in dev_dict or 'category_id' not in dev_dict:
            raise ValueError("Ungültiges Backup: Ein medizinisches Gerät hat keinen Namen, keine Seriennummer oder keine Kategorie-ID.")
        old_id = dev_dict.get('id')
        cat_id = dev_dict.get('category_id')
        rm_id = dev_dict.get('room_id')
        
        if cat_id not in category_map:
            raise ValueError(f"Ungültiges Backup: Gerät '{dev_dict.get('name')}' verweist auf nicht existierende Kategorie-ID {cat_id}.")

        device = MedicalDevice.objects.create(
            name=dev_dict['name'],
            category=category_map[cat_id],
            room=room_map.get(rm_id) if rm_id else None,
            activity_status=dev_dict.get('activity_status', 'active'),
            functional_status=dev_dict.get('functional_status', 'functional'),
            serial_number=dev_dict['serial_number'],
            cohort_device_number=dev_dict.get('cohort_device_number', ''),
            manufacturer=dev_dict.get('manufacturer', ''),
            delivery_date=dev_dict.get('delivery_date'),
            contact_data=dev_dict.get('contact_data', ''),
            notes=dev_dict.get('notes', ''),
        )
        device_map[old_id] = device

    for doc_dict in json_data.get("category_documents", []):
        if not isinstance(doc_dict, dict) or 'title' not in doc_dict or 'category_id' not in doc_dict:
            raise ValueError("Ungültiges Backup: Ein Dokument hat keinen Titel oder keine Kategorie-ID.")
        cat_id = doc_dict.get('category_id')
        dev_id = doc_dict.get('device_id')
        
        if cat_id not in category_map:
            continue

        CategoryDocument.objects.create(
            category=category_map[cat_id],
            device=device_map.get(dev_id) if dev_id else None,
            title=doc_dict['title'],
            document_date=doc_dict.get('document_date'),
            file=doc_dict.get('file', ''),
        )

    for app_dict in json_data.get("device_appointments", []):
        if not isinstance(app_dict, dict) or 'appointment_type' not in app_dict:
            raise ValueError("Ungültiges Backup: Ein Termin hat keinen Typ ('appointment_type' fehlt).")
        dev_id = app_dict.get('medical_device_id')
        if dev_id in device_map:
            DeviceAppointment.objects.create(
                medical_device=device_map[dev_id],
                appointment_type=app_dict['appointment_type'],
                due_date=app_dict['due_date'],
                performed_date=app_dict.get('performed_date'),
                note=app_dict.get('note', ''),
                completed=app_dict.get('completed', False),
            )

    for log_dict in json_data.get("device_audit_logs", []):
        if not isinstance(log_dict, dict) or 'action' not in log_dict:
            continue
        dev_id = log_dict.get('medical_device_id')
        if dev_id in device_map:
            DeviceAuditLog.objects.create(
                medical_device=device_map[dev_id],
                action=log_dict['action'],
                description=log_dict.get('description', ''),
                created_at=log_dict.get('created_at', timezone.now()),
            )

    return {
        "categories": len(category_map),
        "rooms": len(room_map),
        "devices": len(device_map),
        "documents": len(json_data.get("category_documents", [])),
        "appointments": len(json_data.get("device_appointments", [])),
        "audit_logs": len(json_data.get("device_audit_logs", [])),
    }
