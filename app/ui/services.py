import streamlit as st
from app.db.database import SessionLocal, engine, Base
from app.repository.product_repository import ProductRepository
from app.services.product_service import ProductService
from app.services.csv_import_service import CsvImportService
from app.services.purchase_service import PurchaseService


def _ensure_session():
    if "db_session" not in st.session_state:
        Base.metadata.create_all(bind=engine)
        st.session_state.db_session = SessionLocal()
        st.session_state.repository = ProductRepository(st.session_state.db_session)


def get_product_service() -> ProductService:
    _ensure_session()
    if "product_service" not in st.session_state:
        st.session_state.product_service = ProductService(st.session_state.repository)
    return st.session_state.product_service


def get_csv_import_service() -> CsvImportService:
    _ensure_session()
    if "csv_import_service" not in st.session_state:
        st.session_state.csv_import_service = CsvImportService(get_product_service())
    return st.session_state.csv_import_service


def get_purchase_service() -> PurchaseService:
    _ensure_session()
    if "purchase_service" not in st.session_state:
        st.session_state.purchase_service = PurchaseService(st.session_state.repository)
    return st.session_state.purchase_service