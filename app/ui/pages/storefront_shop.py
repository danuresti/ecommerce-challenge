import streamlit as st
from itertools import groupby
from app.ui.services import get_product_service, get_purchase_service
from app.exceptions import NotFoundError, InsufficientStockError, ValidationError, PaymentDeclinedError

st.title("🛍️ Shop")

product_service = get_product_service()
purchase_service = get_purchase_service()

if "flash" in st.session_state:
    col1, col2 = st.columns([20, 1])
    with col1:
        st.success(st.session_state["flash"])
    with col2:
        if st.button("✕", key="dismiss_flash"):
            del st.session_state["flash"]
            st.rerun()

query = st.text_input("Search products", placeholder="Search by name, SKU, or category...")

products = product_service.search(query) if query else product_service.list_products()
products = sorted(products, key=lambda p: ((p.category or "").lower(), p.name.lower()))

if not products:
    st.info("No products found.")
else:
    for category, group in groupby(products, key=lambda p: p.category or "Uncategorized"):
        group_list = list(group)
        with st.expander(f"{category} ({len(group_list)})", expanded=True):
            for product in group_list:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.subheader(product.name)
                        st.caption(f"SKU: {product.sku}")
                        if product.description:
                            st.write(product.description)
                        st.write(f"**${float(product.price):,.2f}** · Stock: {product.stock}")

                    with col2:
                        quantity = st.number_input(
                            "Qty",
                            min_value=1,
                            value=1,
                            step=1,
                            key=f"qty_{product.id}",
                            disabled=product.stock == 0,
                        )
                        total = float(product.price) * quantity
                        st.write(f"Total: **${total:,.2f}**")

                    exceeds_stock = quantity > product.stock

                    with col3:
                        st.write("")
                        buy_clicked = st.button(
                            "Buy",
                            key=f"buy_{product.id}",
                            disabled=product.stock == 0 or exceeds_stock,
                            type="primary",
                        )

                    if product.stock == 0:
                        st.warning("Out of stock.")
                    elif exceeds_stock:
                        st.error(f"Only {product.stock} in stock — reduce quantity to purchase.")

                    if buy_clicked and not exceeds_stock:
                        try:
                            result = purchase_service.purchase(product.id, int(quantity))
                            st.session_state["flash"] = (
                                f"Purchased {result['quantity']}x '{result['product_name']}' "
                                f"for ${result['total']:,.2f}. Transaction: {result['transaction_id'][:8]}..."
                            )
                            st.rerun()
                        except InsufficientStockError as e:
                            st.error(str(e))
                        except PaymentDeclinedError as e:
                            st.error(f"Payment declined: {e}")
                        except (NotFoundError, ValidationError) as e:
                            st.error(str(e))