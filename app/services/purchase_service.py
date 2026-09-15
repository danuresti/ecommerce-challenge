from app.repository.product_repository import ProductRepository
from app.services.payment_gateway import FakePaymentGateway
from app.exceptions import NotFoundError, InsufficientStockError, ValidationError, PaymentDeclinedError


class PurchaseService:
    def __init__(self, repository: ProductRepository, payment_gateway: FakePaymentGateway = None):
        self.repository = repository
        self.payment_gateway = payment_gateway or FakePaymentGateway()

    def purchase(self, product_id: int, quantity: int) -> dict:
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        product = self.repository.get(product_id)
        if product is None:
            raise NotFoundError(f"Product with id {product_id} not found.")

        if product.stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.name}': "
                f"requested {quantity}, available {product.stock}."
            )

        total = float(product.price) * quantity
        payment_result = self.payment_gateway.process_payment(total)

        if not payment_result.success:
            raise PaymentDeclinedError(payment_result.message)

        updated = self.repository.update(product_id, {"stock": product.stock - quantity})

        return {
            "success": True,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": float(product.price),
            "total": total,
            "remaining_stock": updated.stock,
            "transaction_id": payment_result.transaction_id,
        }