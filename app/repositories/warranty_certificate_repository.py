from datetime import date, datetime

from sqlalchemy import select

from app.extensions.database import db
from app.models import Project, WarrantyCertificate


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_warranty_certificate(warranty_certificate_id: int) -> WarrantyCertificate | None:
    return db.session.get(WarrantyCertificate, warranty_certificate_id)


def get_warranty_certificate_by_project_id(project_id: int) -> WarrantyCertificate | None:
    stmt = (
        select(WarrantyCertificate)
        .where(WarrantyCertificate.project_id == project_id)
        .order_by(WarrantyCertificate.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_warranty_certificates(
    project_id: int | None = None,
    po_no: str | None = None,
    invoice_no: str | None = None,
) -> list[WarrantyCertificate]:
    stmt = select(WarrantyCertificate).order_by(WarrantyCertificate.id.desc())

    if project_id is not None:
        stmt = stmt.where(WarrantyCertificate.project_id == project_id)
    if po_no is not None:
        stmt = stmt.where(WarrantyCertificate.po_no == po_no)
    if invoice_no is not None:
        stmt = stmt.where(WarrantyCertificate.invoice_no == invoice_no)

    return list(db.session.execute(stmt).scalars().all())


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_date_val(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    if 'T' in s:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).date()
    return date.fromisoformat(s[:10])


def create_warranty_certificate(*, data: dict) -> WarrantyCertificate:
    cert_date = _parse_date_val(data.get('certificate_date'))
    po_date_val = _parse_date_val(data.get('po_date'))
    inv_date_val = _parse_date_val(data.get('invoice_date'))

    po_no_val = _normalize_optional_string(
        data.get('po_no') or data.get('po_number')
    )
    invoice_no_val = _normalize_optional_string(
        data.get('invoice_no') or data.get('invoice_number')
    )
    remark_val = _normalize_optional_string(
        data.get('remark') or data.get('remarks')
    )

    cert = WarrantyCertificate(
        project_id=data['project_id'],
        certificate_date=cert_date,
        warranty_period=str(data.get('warranty_period', '')).strip(),
        po_no=po_no_val,
        po_date=po_date_val,
        invoice_no=invoice_no_val,
        invoice_date=inv_date_val,
        remark=remark_val,
    )
    db.session.add(cert)
    db.session.flush()
    return cert


def update_warranty_certificate(
    cert: WarrantyCertificate,
    data: dict,
) -> WarrantyCertificate:
    if 'project_id' in data:
        cert.project_id = data['project_id']

    if 'certificate_date' in data:
        dt = _parse_date_val(data.get('certificate_date'))
        if dt is not None:
            cert.certificate_date = dt

    if 'warranty_period' in data and data['warranty_period'] is not None:
        cert.warranty_period = str(data['warranty_period']).strip()

    if 'po_no' in data or 'po_number' in data:
        cert.po_no = _normalize_optional_string(
            data.get('po_no') or data.get('po_number')
        )

    if 'po_date' in data:
        cert.po_date = _parse_date_val(data.get('po_date'))

    if 'invoice_no' in data or 'invoice_number' in data:
        cert.invoice_no = _normalize_optional_string(
            data.get('invoice_no') or data.get('invoice_number')
        )

    if 'invoice_date' in data:
        cert.invoice_date = _parse_date_val(data.get('invoice_date'))

    if 'remark' in data or 'remarks' in data:
        cert.remark = _normalize_optional_string(
            data.get('remark') or data.get('remarks')
        )

    cert.updated_at = datetime.utcnow()
    db.session.flush()
    return cert


def delete_warranty_certificate(warranty_certificate_id: int) -> list[str]:
    cert = get_warranty_certificate(warranty_certificate_id)
    if cert is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type='warranty_certificate',
        entity_id=warranty_certificate_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(cert)
    db.session.flush()
    return storage_keys
