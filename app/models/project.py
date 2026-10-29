from datetime import datetime

from app.extensions.database import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_code = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )

    project_title = db.Column(
        db.String(255),
        nullable=False,
    )

    nickname = db.Column(
        db.String(255),
        nullable=True,
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    customer = db.relationship(
        "Customer",
        back_populates="projects",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="projects",
    )

    customer_queries = db.relationship(
        "CustomerQuery",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    quotation_requests = db.relationship(
        "QuotationRequest",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_quotations = db.relationship(
        "SupplierQuotation",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    cost_sheets = db.relationship(
        "CostSheet",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="CostSheet.version_number.desc()",
    )

    pre_qualification_bids = db.relationship(
        "PreQualificationBid",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    pqb_bid_documents = db.relationship(
        "PqbBidDocument",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    corrigendums = db.relationship(
        "Corrigendum",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    limited_tender_enquiries = db.relationship(
        "LimitedTenderEnquiry",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    notification_awards = db.relationship(
        "NotificationAward",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    consultancy_invoices = db.relationship(
        "ConsultancyInvoice",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    expressions_of_interest = db.relationship(
        "ExpressionOfInterest",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customer_quotations = db.relationship(
        "CustomerQuotation",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customer_tenders = db.relationship(
        "CustomerTender",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    bid_submissions = db.relationship(
        "BidSubmission",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    purchase_orders = db.relationship(
        "PurchaseOrder",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_order_confirmations = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_proforma_invoices = db.relationship(
        "SupplierProformaInvoice",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_invoices = db.relationship(
        "SupplierInvoice",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_packing_lists = db.relationship(
        "SupplierPackingList",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    import_logistics = db.relationship(
        "ImportLogistics",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    bills_of_entry = db.relationship(
        "BillOfEntry",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customs_clearances = db.relationship(
        "CustomsClearance",
        overlaps="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customer_delivery_invoices = db.relationship(
        "CustomerDeliveryInvoice",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customer_delivery_packing_lists = db.relationship(
        "CustomerDeliveryPackingList",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    delivery_challans = db.relationship(
        "DeliveryChallan",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    warranty_certificates = db.relationship(
        "WarrantyCertificate",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    transport_details = db.relationship(
        "TransportDetail",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    customer_payments = db.relationship(
        "CustomerPayment",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    supplier_payments = db.relationship(
        "SupplierPayment",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    bid_document_techno_commercials = db.relationship(
        "BidDocumentTechnoCommercial",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    techno_commercial_tenders = db.relationship(
        "TechnoCommercialTender",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    bid_document_ltes = db.relationship(
        "BidDocumentLte",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    eway_bills = db.relationship(
        "EWayBill",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    steps = db.relationship(
        "ProjectStep",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ProjectStep.step_number",
    )

    step_remarks = db.relationship(
        "StepRemark",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="StepRemark.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.project_title}>"
