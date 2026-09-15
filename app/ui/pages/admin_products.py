import streamlit as st
from app.ui.services import get_product_service
from app.exceptions import ValidationError, DuplicateError, NotFoundError

st.title("🔧 Manage Products")

product_service = get_product_service()

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon="✅")

section = st.radio(
    "Section",
    ["View All", "Create", "Edit / Delete"],
    horizontal=True,
    label_visibility="collapsed",
    key="products_section",
)

if section == "View All":
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

elif section == "Create":
    with st.form("create_product_form", clear_on_submit=True):
        name = st.text_input("Name")
        sku = st.text_input("SKU")
        description = st.text_area("Description")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, step=0.01)
        stock = st.number_input("Stock", min_value=0, step=1)
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.1)

        submitted = st.form_submit_button("Create Product")

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
                st.session_state["flash"] = f"Product '{name}' created successfully."
                st.rerun()
            except (ValidationError, DuplicateError) as e:
                st.error(str(e))

elif section == "Edit / Delete":
    products = product_service.list_products()
    if not products:
        st.info("No products to edit.")
    else:
        options = {f"{p.id} — {p.name} ({p.sku})": p.id for p in products}
        selected_label = st.selectbox("Select a product", list(options.keys()))
        selected_id = options[selected_label]
        product = product_service.get_product(selected_id)

        with st.form("edit_product_form"):
            name = st.text_input("Name", value=product.name)
            price = st.number_input("Price", min_value=0.0, step=0.01, value=float(product.price))
            stock = st.number_input("Stock", min_value=0, step=1, value=product.stock)

            col1, col2 = st.columns(2)
            with col1:
                update_submitted = st.form_submit_button("Update Product")
            with col2:
                delete_submitted = st.form_submit_button("Delete Product", type="secondary")

            if update_submitted:
                try:
                    product_service.update_product(selected_id, {
                        "name": name,
                        "price": price,
                        "stock": int(stock),
                    })
                    st.session_state["flash"] = "Product updated."
                    st.rerun()
                except (ValidationError, DuplicateError, NotFoundError) as e:
                    st.error(str(e))

            if delete_submitted:
                try:
                    product_service.delete_product(selected_id)
                    st.session_state["flash"] = "Product deleted."
                    st.rerun()
                except NotFoundError as e:
                    st.error(str(e))