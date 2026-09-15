import streamlit as st
from app.ui.services import get_product_service
from app.ui.components import show_flash
from app.exceptions import ValidationError, DuplicateError, NotFoundError

st.title("🔧 Manage Products")

product_service = get_product_service()

show_flash()

tab_list, tab_create, tab_edit = st.tabs(
    ["View All", "Create", "Edit / Delete"],
    key="products_tab",
    on_change="rerun",
)

with tab_list:
    products = product_service.list_products()
    if not products:
        st.info("No products yet.")
    else:
        st.dataframe(
            [
                {
                    "ID": p.id,
                    "Name": p.name,
                    "SKU": p.sku,
                    "Category": p.category,
                    "Price": float(p.price),
                    "Stock": p.stock,
                    "Weight (kg)": float(p.weight_kg) if p.weight_kg else None,
                }
                for p in products
            ],
            use_container_width=True,
        )

with tab_create:
    if "create_message" in st.session_state:
        col1, col2 = st.columns([20, 1])
        with col1:
            st.success(st.session_state["create_message"])
        with col2:
            if st.button("✕", key="dismiss_create_message"):
                pass
        del st.session_state["create_message"]

    with st.form("create_product_form", clear_on_submit=True):
        name = st.text_input("Name")
        sku = st.text_input("SKU")
        description = st.text_area("Description")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, step=0.01)
        stock = st.number_input("Stock", min_value=0, step=1)
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.1)

        submitted = st.form_submit_button("Create Product", type="primary")

        if submitted:
            try:
                product_service.create_product({
                    "name": name,
                    "sku": sku,
                    "description": description,
                    "category": category,
                    "price": price,
                    "stock": int(stock),
                    "weight_kg": weight_kg,
                })
                st.session_state["create_message"] = f"Product '{name}' created successfully."
                st.rerun()
            except (ValidationError, DuplicateError) as e:
                st.error(str(e))

with tab_edit:
    products = product_service.list_products()
    if not products:
        st.info("No products to edit.")
    else:
        options = {f"{p.id} — {p.name} ({p.sku})": p.id for p in products}
        selected_label = st.selectbox("Select a product", list(options.keys()))
        selected_id = options[selected_label]
        product = product_service.get_product(selected_id)

        if "edit_message" in st.session_state:
            col1, col2 = st.columns([20, 1])
            with col1:
                st.success(st.session_state["edit_message"])
            with col2:
                if st.button("✕", key="dismiss_edit_message"):
                    pass
            del st.session_state["edit_message"]

        with st.form("edit_product_form"):
            name = st.text_input("Name", value=product.name)
            sku = st.text_input("SKU", value=product.sku)
            category = st.text_input("Category", value=product.category or "")
            price = st.number_input("Price", min_value=0.0, step=0.01, value=float(product.price))
            stock = st.number_input("Stock", min_value=0, step=1, value=product.stock)
            weight_kg = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                step=0.1,
                value=float(product.weight_kg) if product.weight_kg else 0.0,
            )

            col1, col2 = st.columns(2)
            with col1:
                update_submitted = st.form_submit_button("Update Product", type="primary")
            with col2:
                delete_submitted = st.form_submit_button("Delete Product", type="secondary")

            if update_submitted:
                try:
                    product_service.update_product(selected_id, {
                        "name": name,
                        "sku": sku,
                        "category": category,
                        "price": price,
                        "stock": int(stock),
                        "weight_kg": weight_kg,
                    })
                    st.session_state["edit_message"] = f"Product '{name}' updated."
                    st.rerun()
                except (ValidationError, DuplicateError, NotFoundError) as e:
                    st.error(str(e))

            if delete_submitted:
                try:
                    product_service.delete_product(selected_id)
                    st.session_state["flash"] = f"Product '{product.name}' deleted."
                    st.rerun()
                except NotFoundError as e:
                    st.error(str(e))