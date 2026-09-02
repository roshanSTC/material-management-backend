from datetime import datetime

from app.extensions.database import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_title = db.Column(
        db.String(255),
        nullable=False,
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
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
        lazy="select",
    )
    
    quotation_requests = db.relationship(
        "QuotationRequest",
        back_populates="project",
        lazy="select",
    )

    supplier_quotations = db.relationship(
        "SupplierQuotation",
        back_populates="project",
        lazy="select",
    )

    cost_sheets = db.relationship(
        "CostSheet",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="CostSheet.version_number.desc()",
    )

    customer_quotations = db.relationship(
        "CustomerQuotation",
        back_populates="project",
        lazy="select",
    )
    
    customer_tenders = db.relationship(
        "CustomerTender",
        back_populates="project",
        lazy="select",
    )

    bid_submissions = db.relationship(
        "BidSubmission",
        back_populates="project",
        lazy="select",
    )

    purchase_orders = db.relationship(
        "PurchaseOrder",
        back_populates="project",
        lazy="select",
    )

    supplier_order_confirmations = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="project",
        lazy="select",
    )
    
    customer_delivery_invoices = db.relationship(
        "CustomerDeliveryInvoice",
        back_populates="project",
        lazy="select",
    )
    
    customer_delivery_packing_lists = db.relationship(
        "CustomerDeliveryPackingList",
        back_populates="project",
        lazy="select",
    )
    
    delivery_challans = db.relationship(
        "DeliveryChallan",
        back_populates="project",
        lazy="select",
    )
    
    warranty_certificates = db.relationship(
        "WarrantyCertificate",
        back_populates="project",
        lazy="select",
    )
    
    transport_details = db.relationship(
        "TransportDetail",
        back_populates="project",
        lazy="select",
    )
    
    customer_payments = db.relationship(
        "CustomerPayment",
        back_populates="project",
        lazy="select",
    )

    supplier_payments = db.relationship(
        "SupplierPayment",
        back_populates="project",
        lazy="select",
    )
    
    
    steps = db.relationship(
        "ProjectStep",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ProjectStep.step_number",
    )





    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.project_title}>"
