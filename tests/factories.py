"""
Test Factory to make fake objects for testing
"""

import factory
from factory.fuzzy import FuzzyChoice, FuzzyInteger
from service.models import InventoryItem, Condition


class InventoryItemFactory(factory.Factory):
    """Creates fake inventory items for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = InventoryItem

    id = factory.Sequence(lambda n: n)
    product_id = factory.Sequence(lambda n: f"PROD{n:04d}")
    quantity = FuzzyInteger(0, 100)
    restock_level = FuzzyInteger(5, 25)
    restock_amount = FuzzyInteger(10, 50)
    condition = FuzzyChoice(choices=[Condition.NEW, Condition.OPEN_BOX, Condition.USED])
