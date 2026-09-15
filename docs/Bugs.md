# Bugs & Issues Log

## 1. Falsy value bug: `price = 0.00` incorrectly rejected as "missing required field"

**Error (surfaced during CSV import testing):**
```
Row 47: Missing required fields: price
```
despite `price` being present in the CSV with value `0.00` (a legitimate free/promotional item — "Mystery Box" in the test dataset).

**Cause:**
`ProductService._validate_product_data` checked for missing required fields using `if not data.get(f)`. In Python, `not 0.0` evaluates to `True`, so a valid price of `0` was treated as if it were absent.

**Fix:**
Replaced the falsy check with an explicit `_is_missing()` helper that distinguishes `None` and empty/whitespace-only strings (genuinely missing) from valid falsy values like `0` or `0.0` (legitimate data). Confirmed as a product decision: a price of exactly `$0.00` is valid.

---

## 2. CSV import — data cleaning decisions (not bugs, but worth documenting)

The provided example CSV was intentionally adversarial, testing the import pipeline against multiple edge cases:

| Case | Handling |
|------|----------|
| `price` with currency symbol (e.g. `"$29.99"`) | Stripped (`$`, `,`) and parsed as a valid float, rather than rejected |
| `price` as non-numeric text (e.g. `"free"`) | Rejected — not a recoverable numeric format |
| Negative `stock` | Rejected via business validation (`ValidationError`) |
| Empty or whitespace-only `name` | Rejected as missing required field |
| Fully blank rows | Detected explicitly and skipped, rather than silently producing a "phantom" product with `NaN` price |
| Empty cell read by pandas as `NaN` | Explicitly converted to `""` (not the literal string `"nan"`) before validation, so required-field checks work correctly |
| Duplicate SKUs within the same CSV | First occurrence imported; subsequent duplicates rejected via `DuplicateError`, same as any other creation path |
| Optional `weight_kg` left blank | Accepted, stored as `None` |

## Security considerations validated against test data

The provided CSV included adversarial test rows (an XSS payload and a SQL injection string, both used as product names). Both were handled safely without any special-casing required:

- **SQL injection:** no risk — SQLAlchemy's ORM uses parameterized queries, not raw string concatenation, so the malicious string is stored and retrieved as inert text.
- **XSS:** Streamlit escapes HTML by default in its rendering components (`st.write`, `st.dataframe`, etc.). The UI layer avoids `unsafe_allow_html=True` anywhere, so injected markup is never rendered as live HTML.

---

## 3. `ModuleNotFoundError: No module named 'app'` when running Streamlit directly

**Error:**
```
from app.ui.services import get_product_service, get_csv_import_service, get_purchase_service
ModuleNotFoundError: No module named 'app'
```

**Cause:**
Running `streamlit run app/ui/streamlit_app.py` directly adds the script's own directory (`app/ui/`) to Python's module search path, not the project root. Since `app` is a package rooted at the project root, absolute imports like `from app.ui.services import ...` failed to resolve.

**Fix:**
Run Streamlit via `python -m streamlit run app/ui/streamlit_app.py` instead. Using `-m` adds the current working directory (the project root) to the search path rather than the script's directory. The Dockerfile's `CMD` uses the same `python -m streamlit run ...` form for the same reason.

---

## 4. `st.tabs()` loses selection on every rerun

**Bug:**
While on the "Edit / Delete" tab, selecting a different product from the dropdown (which triggers a rerun, like any widget interaction in Streamlit) caused the UI to jump back to the first tab ("View All"), and any pending flash message was lost with it.

**Cause:**
`st.tabs()` does not persist which tab is active across reruns — every rerun redraws the first tab by default. Since *any* widget interaction (not just tab clicks) triggers a full script rerun in Streamlit, this made multi-step workflows within a tabbed section unusable.

**Fix:**
Replaced `st.tabs([...])` with `st.radio([...], horizontal=True, key="products_section")`. Because `st.radio` is a regular stateful widget tied to a `key`, Streamlit persists its selected value across reruns the same way it does for any other widget (e.g., the product `selectbox`), keeping the user on the same section after an interaction.
