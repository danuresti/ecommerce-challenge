import random
import uuid
from dataclasses import dataclass

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    message: str


class FakePaymentGateway:
    FAILURE_RATE = 0.1

    def process_payment(self, amount: float) -> PaymentResult:
        if random.random() < self.FAILURE_RATE:
            return PaymentResult(
                success=False,
                transaction_id="",
                message="Payment declined by provider (simulated failure).",
            )
        return PaymentResult(
            success=True,
            transaction_id=str(uuid.uuid4()),
            message="Payment approved.",
        )