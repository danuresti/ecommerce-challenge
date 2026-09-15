import streamlit as st
from app.ui.services import get_product_service, get_csv_import_service, get_purchase_service

st.set_page_config(page_title="E-Commerce Challenge", page_icon="🛒", layout="wide")

get_product_service()
get_csv_import_service()
get_purchase_service()

admin_products = st.Page("pages/admin_products.py", title="Manage Products", icon="🔧")
admin_import_csv = st.Page("pages/admin_import_csv.py", title="Import CSV", icon="📥")
storefront_search = st.Page("pages/storefront_search.py", title="Search Products", icon="🔍")
storefront_purchase = st.Page("pages/storefront_purchase.py", title="Purchase", icon="🛍️")

pg = st.navigation({
    "Admin": [admin_products, admin_import_csv],
    "Storefront": [storefront_search, storefront_purchase],
})

pg.run()