import logging
import streamlit as st
import tempfile
import os
from app.ui.services import get_csv_import_service
from app.ui.components import show_flash
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

st.title("📥 Import Products from CSV")

csv_import_service = get_csv_import_service()

show_flash()

st.write("Upload a CSV file with columns: `name`, `sku`, `description`, `category`, `price`, `stock`, `weight_kg`.")

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