import logging
import tempfile
import os
import streamlit as st
from app.ui.services import get_product_service, get_csv_import_service
from app.ui.components import show_flash
from app.core.exceptions import ValidationError, DuplicateError, NotFoundError

logger = logging.getLogger(__name__)

st.title("🔧 Manage Products")

product_service = get_product_service()
csv_import_service = get_csv_import_service()

show_flash()

tab_list, tab_create, tab_edit, tab_import = st.tabs(
    ["View All", "Create", "Edit / Delete", "Import CSV"],
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
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Weight (kg)": st.column_config.NumberColumn(format="%.3f kg"),
            },
            width="stretch",
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
        price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
        stock = st.number_input("Stock", min_value=0, step=1)
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.001, format="%.3f")

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
            except Exception as e:
                logger.exception(f"Unexpected error creating product: sku={sku}")
                st.error("An unexpected error occurred. Please try again.")

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
            price = st.number_input(
                "Price", min_value=0.0, step=0.01, format="%.2f", value=float(product.price)
            )
            stock = st.number_input("Stock", min_value=0, step=1, value=product.stock)
            weight_kg = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                step=0.05,
                format="%.3f",
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
                except Exception as e:
                    logger.exception(f"Unexpected error updating product: id={selected_id}")
                    st.error("An unexpected error occurred. Please try again.")

            if delete_submitted:
                try:
                    product_service.delete_product(selected_id)
                    st.session_state["flash"] = f"Product '{product.name}' deleted."
                    st.rerun()
                except NotFoundError as e:
                    st.error(str(e))
                except Exception as e:
                    logger.exception(f"Unexpected error deleting product: id={selected_id}")
                    st.error("An unexpected error occurred. Please try again.")

with tab_import:
    st.write(
        "Upload a CSV file with columns: `name`, `sku`, `description`, `category`, "
        "`price`, `stock`, `weight_kg`."
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        if st.button("Import", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                result = csv_import_service.import_from_csv(tmp_path)

                st.session_state["flash"] = (
                    f"Import complete: {result.imported} imported, "
                    f"{result.skipped} skipped, out of {result.total_rows} total rows."
                )

                if result.errors:
                    st.session_state["import_errors"] = result.errors
                elif "import_errors" in st.session_state:
                    del st.session_state["import_errors"]

                st.rerun()
            except ValidationError as e:
                st.error(f"Import failed: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error during CSV import: file={uploaded_file.name}")
                st.error("An unexpected error occurred during import. Please try again.")
            finally:
                os.remove(tmp_path)

    if "import_errors" in st.session_state:
        header_col, close_col = st.columns([20, 1])
        with header_col:
            st.subheader(f"{len(st.session_state['import_errors'])} error(s) from last import")
        with close_col:
            if st.button("✕", key="dismiss_import_errors"):
                del st.session_state["import_errors"]
                st.rerun()

        with st.expander("View details", expanded=True):
            for error in st.session_state["import_errors"]:
                st.write(f"- {error}")