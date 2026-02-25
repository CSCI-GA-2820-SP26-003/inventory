"""
Models for InventoryItem

All of the models are stored in this module
"""

import enum
import logging
import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Condition(enum.Enum):
    """Enumeration of valid inventory item conditions"""

    NEW = "NEW"
    OPEN_BOX = "OPEN_BOX"
    USED = "USED"


class InventoryItem(db.Model):
    """
    Class that represents an InventoryItem
    """

    __tablename__ = "inventory_item"

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    product_id = db.Column(db.String(63), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    restock_level = db.Column(db.Integer, nullable=False)
    restock_amount = db.Column(db.Integer, nullable=False)
    condition = db.Column(
        db.Enum(Condition, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("product_id", "condition", name="uq_product_condition"),
        db.CheckConstraint("quantity >= 0", name="ck_quantity_non_negative"),
    )

    def __repr__(self):
        return (
            f"<InventoryItem {self.product_id} [{self.condition.value}] id=[{self.id}]>"
        )

    def create(self):
        """
        Creates an InventoryItem to the database
        """
        logger.info("Creating inventory item for product %s", self.product_id)
        self.id = None  # pylint: disable=invalid-name
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates an InventoryItem to the database
        """
        logger.info("Saving inventory item %s", self.product_id)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes an InventoryItem from the data store"""
        logger.info("Deleting inventory item %s", self.product_id)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes an InventoryItem into a dictionary"""
        return {
            "id": self.id,
            "public_id": self.public_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "restock_level": self.restock_level,
            "restock_amount": self.restock_amount,
            "condition": self.condition.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def deserialize(self, data):
        """
        Deserializes an InventoryItem from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.product_id = data["product_id"]
            self.quantity = data.get("quantity", 0)
            self.restock_level = data["restock_level"]
            self.restock_amount = data["restock_amount"]
            self.condition = Condition(data["condition"])
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid InventoryItem: missing " + error.args[0]
            ) from error
        except ValueError as error:
            raise DataValidationError("Invalid InventoryItem: " + str(error)) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid InventoryItem: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the InventoryItems in the database"""
        logger.info("Processing all InventoryItems")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds an InventoryItem by its ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, product_id):
        """Returns all InventoryItems with the given product_id

        Args:
            product_id (string): the product_id of the InventoryItems you want to match
        """
        logger.info("Processing product_id query for %s ...", product_id)
        return cls.query.filter(cls.product_id == product_id)

    @classmethod
    def find_by_condition(cls, condition):
        """Returns all InventoryItems with the given condition

        Args:
            condition (Condition): the condition to filter by
        """
        logger.info("Processing condition query for %s ...", condition.value)
        return cls.query.filter(cls.condition == condition)

    @classmethod
    def find_by_public_id(cls, public_id):
        """Finds an InventoryItem by its public_id"""
        logger.info("Processing lookup for public_id %s ...", public_id)
        return cls.query.filter(cls.public_id == public_id).first()
