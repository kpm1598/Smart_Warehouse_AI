"""SQLAlchemy models for the five warehouse tables (TDD section 6)."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from backend.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True)
    # COLLATE NOCASE makes the unique constraint case-insensitive.
    name = Column(String(collation="NOCASE"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    inventory_rows = relationship("Inventory", back_populates="product")
    movements = relationship("StockMovement", back_populates="product")


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint("max_capacity >= 0", name="ck_location_max_nonneg"),
        CheckConstraint(
            "occupied_capacity >= 0 AND occupied_capacity <= max_capacity",
            name="ck_location_occupied_range",
        ),
    )

    location_id = Column(Integer, primary_key=True)
    location_code = Column(String, nullable=False, unique=True)
    max_capacity = Column(Integer, nullable=False)
    occupied_capacity = Column(Integer, nullable=False, default=0)
    row_number = Column(Integer, nullable=False)
    column_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    inventory_rows = relationship("Inventory", back_populates="location")

    @property
    def remaining_capacity(self):
        return self.max_capacity - self.occupied_capacity


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_inventory_product_location"),
        CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),
    )

    inventory_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory_rows")
    location = relationship("Location", back_populates="inventory_rows")


class WarehouseConnection(Base):
    __tablename__ = "warehouse_connections"
    __table_args__ = (
        UniqueConstraint(
            "source_location_id", "destination_location_id", name="uq_connection_pair"
        ),
        CheckConstraint("distance > 0", name="ck_connection_distance_positive"),
    )

    connection_id = Column(Integer, primary_key=True)
    source_location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    destination_location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    distance = Column(Float, nullable=False, default=1.0)
    is_blocked = Column(Boolean, nullable=False, default=False)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("movement_type IN ('IN', 'OUT')", name="ck_movement_type"),
        CheckConstraint("quantity > 0", name="ck_movement_quantity_positive"),
    )

    movement_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    movement_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="movements")
    location = relationship("Location")
