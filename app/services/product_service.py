from app.repository.product_repository import ProductRepository
from app.models.product import Product
from app.exceptions import NotFoundError, ValidationError, DuplicateError


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def create_product(self, data: dict) -> Product:
        self._validate_product_data(data)

        existing = self.repository.get_by_sku(data["sku"])
        if existing is not None:
            raise DuplicateError(f"SKU '{data['sku']}' already exists.")

        product = Product(**data)
        return self.repository.create(product)

    def update_product(self, product_id: int, data: dict) -> Product:
        self._validate_product_data(data, partial=True)

        if "sku" in data:
            existing = self.repository.get_by_sku(data["sku"])
            if existing is not None and existing.id != product_id:
                raise DuplicateError(f"SKU '{data['sku']}' already exists.")

        updated = self.repository.update(product_id, data)
        if updated is None:
            raise NotFoundError(f"Product with id {product_id} not found.")
        return updated

    def delete_product(self, product_id: int) -> bool:
        deleted = self.repository.delete(product_id)
        if not deleted:
            raise NotFoundError(f"Product with id {product_id} not found.")
        return deleted

    def get_product(self, product_id: int) -> Product:
        product = self.repository.get(product_id)
        if product is None:
            raise NotFoundError(f"Product with id {product_id} not found.")
        return product

    def list_products(self) -> list[Product]:
        return self.repository.list()

    def search(self, query: str) -> list[Product]:
        all_products = self.repository.list()
        query_lower = query.lower()
        return [
            p for p in all_products
            if query_lower in p.name.lower()
            or query_lower in (p.category or "").lower()
            or query_lower in p.sku.lower()
        ]

    def _validate_product_data(self, data: dict, partial: bool = False) -> None:
        if not partial or "price" in data:
            if data.get("price") is not None and data["price"] < 0:
                raise ValidationError("Price cannot be negative.")

        if not partial or "stock" in data:
            if data.get("stock") is not None and data["stock"] < 0:
                raise ValidationError("Stock cannot be negative.")

        if not partial or "weight_kg" in data:
            weight = data.get("weight_kg")
            if weight is not None and weight < 0:
                raise ValidationError("Weight cannot be negative.")

        if not partial:
            required_fields = ["name", "sku", "price"]
            missing = [f for f in required_fields if self._is_missing(data.get(f))]
            if missing:
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    def _is_missing(self, value) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False