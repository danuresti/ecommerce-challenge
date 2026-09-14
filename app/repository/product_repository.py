from sqlalchemy.orm import Session
from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.query(Product).filter(Product.sku == sku).first()

    def list(self) -> list[Product]:
        return self.db.query(Product).all()

    def update(self, product_id: int, data: dict) -> Product | None:
        product = self.get(product_id)
        if product is None:
            return None
        for key, value in data.items():
            setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product_id: int) -> bool:
        product = self.get(product_id)
        if product is None:
            return False
        self.db.delete(product)
        self.db.commit()
        return True