import streamlit as st
from app.core.logging_config import configure_logging
from app.ui.services import get_product_service, get_csv_import_service, get_purchase_service

configure_logging()

st.set_page_config(page_title="E-Commerce Challenge", page_icon="🛒", layout="wide")

get_product_service()
get_csv_import_service()
get_purchase_service()

admin_products = st.Page("pages/admin_products.py", title="Manage Products", icon="🔧")
storefront_shop = st.Page("pages/storefront_shop.py", title="Shop", icon="🛍️")

pg = st.navigation({
    "Admin": [admin_products],
    "Shop": [storefront_shop],
})

pg.run()