import streamlit as st
from itertools import groupby
from app.ui.services import get_product_service, get_purchase_service
from app.exceptions import NotFoundError, InsufficientStockError, ValidationError, PaymentDeclinedError

st.title("🛍️ Shop")

product_service = get_product_service()
purchase_service = get_purchase_service()

if "last_message" not in st.session_state:
    st.session_state.last_message = None  # (product_id, type, text)


def clear_last_message():
    st.session_state.last_message = None


@st.dialog("Confirm Purchase")
def confirm_purchase(product_id, product_name, quantity, total):
    st.write(f"Purchase {quantity}x '{product_name}' for **${total:,.2f}**?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm", type="primary"):
            try:
                result = purchase_service.purchase(product_id, quantity)
                st.session_state.last_message = (
                    product_id,
                    "success",
                    f"Purchased {result['quantity']}x for ${result['total']:,.2f}. "
                    f"Transaction: {result['transaction_id'][:8]}...",
                )
            except InsufficientStockError as e:
                st.session_state.last_message = (product_id, "error", str(e))
            except PaymentDeclinedError as e:
                st.session_state.last_message = (product_id, "error", f"Payment declined: {e}")
            except (NotFoundError, ValidationError) as e:
                st.session_state.last_message = (product_id, "error", str(e))
            st.rerun()
    with col2:
        if st.button("Cancel"):
            st.rerun()


def clear_search():
    st.session_state.search_query = ""


search_col, search_btn_col, clear_btn_col = st.columns([4, 1, 1])
with search_col:
    query = st.text_input(
        "Search products",
        placeholder="Search by name, SKU, or category...",
        label_visibility="collapsed",
        key="search_query",
    )
with search_btn_col:
    st.button("Search", use_container_width=True)
with clear_btn_col:
    st.button("Clear", use_container_width=True, on_click=clear_search)

products = product_service.search(query) if query else product_service.list_products()
products = sorted(products, key=lambda p: ((p.category or "").lower(), p.name.lower()))

if not products:
    st.info("No products found.")
else:
    categories = sorted(set(p.category or "Uncategorized" for p in products))

    with st.container(horizontal=True):
        if st.button("Expand All"):
            for cat in categories:
                st.session_state[f"cat_expanded_{cat}"] = True
        if st.button("Collapse All"):
            for cat in categories:
                st.session_state[f"cat_expanded_{cat}"] = False

    for category, group in groupby(products, key=lambda p: p.category or "Uncategorized"):
        group_list = list(group)
        exp_key = f"cat_expanded_{category}"
        with st.expander(
            f"{category} ({len(group_list)})",
            expanded=st.session_state.get(exp_key, True),
            key=exp_key,
            on_change="rerun",
        ):
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
                            on_click=clear_last_message,
                        )

                    if product.stock == 0:
                        st.warning("Out of stock.")
                    elif exceeds_stock:
                        st.error(f"Only {product.stock} in stock — reduce quantity to purchase.")

                    if buy_clicked and not exceeds_stock:
                        confirm_purchase(product.id, product.name, int(quantity), total)

                    if st.session_state.last_message and st.session_state.last_message[0] == product.id:
                        _, msg_type, msg_text = st.session_state.last_message
                        msg_col1, msg_col2 = st.columns([20, 1])
                        with msg_col1:
                            (st.success if msg_type == "success" else st.error)(msg_text)
                        with msg_col2:
                            if st.button("✕", key=f"dismiss_{product.id}"):
                                st.session_state.last_message = None
                                st.rerun()