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

**UI note:** the import error list (shown after a CSV import with skipped rows) has a manual dismiss button, consistent with the dismiss pattern used for confirmation messages elsewhere in the UI (see Design Decisions #12, #14). A successful import with zero errors also automatically clears any leftover error list from a previous import.

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
By default, `st.tabs()` does not track which tab is active — every rerun redraws the first tab. Since *any* widget interaction (not just tab clicks) triggers a full script rerun in Streamlit, this made multi-step workflows within a tabbed section unusable.

**Initial workaround:** replaced `st.tabs()` with `st.radio([...], horizontal=True, key=...)`, since a keyed widget persists its value across reruns.

**Final fix:** the installed Streamlit version (1.63.0) supports state tracking natively on `st.tabs()` via the `key` and `on_change="rerun"` parameters. Reverted to `st.tabs(["View All", "Create", "Edit / Delete"], key="products_tab", on_change="rerun")`, which persists the active tab, restoring the original visual style without the earlier bug.

---

## 5. `number_input` with `max_value` silently rejects a valid quantity check without updating state

**Bug:**
On the Shop page, typing a quantity greater than available stock (e.g. `10` when stock is `5`) into a `number_input` with `max_value=product.stock` showed a validation error visually, but: (a) the "Buy" button remained enabled and a purchase could still be submitted, and (b) a live total computed from the same `quantity` variable did not update to reflect the typed value.

**Cause:**
When `max_value` is set, Streamlit's frontend intercepts an out-of-range typed value before it reaches the Python-side variable — the widget's return value silently stays at the last *valid* value rather than reflecting what the user actually typed. Downstream code (`exceeds_stock = quantity > product.stock`, the live total) never saw the real input, so both checks incorrectly evaluated against a stale, valid-looking quantity.

**Fix:**
Removed `max_value` from the `number_input` entirely and implemented the validation explicitly in application code: `exceeds_stock = quantity > product.stock`, computed after reading `quantity` unconstrained. This value now drives (1) disabling the "Buy" button, (2) an explicit error message, and (3) a defensive re-check (`if buy_clicked and not exceeds_stock:`) before calling `PurchaseService.purchase()`.

---

## 6. `st.toast()` does not reliably update across `st.rerun()` calls

**Bug:**
Using `st.toast()` for purchase/update/delete confirmations (via a `st.session_state["flash"]` pattern, shown at the top of the script and popped after display) worked for a single action, but if a toast was still visible on screen when a second action occurred, the toast did not update to the new message — the old text remained displayed.

**Investigation:**
- Streamlit's official docs describe an "update a toast message" pattern: assign `msg = st.toast(...)`, then call `msg.toast(...)` later to update the same toast *in place*, explicitly noting "if a toast has already disappeared or been dismissed, the update will not be seen."
- A related official issue ([streamlit/streamlit#7740](https://github.com/streamlit/streamlit/issues/7740), "Toasts are not preserved when page is rerun") confirms `st.toast()` combined with a programmatic rerun (`st.rerun()`) is a known source of unreliable toast behavior — not an isolated case.
- **Attempted fix:** stored the toast handle in `st.session_state` (`st.session_state.toast_handle = st.toast(...)`) and called `.toast()` on the stored handle for subsequent updates, following the documented "update" pattern. This did **not** resolve the issue — the handle does not survive a full script rerun in a way that lets the frontend recognize it as the same toast, since `st.rerun()` rebuilds the entire element tree from scratch each execution.

**Resolution:**
The resolution differs by page based on realistic usage risk:
- **Shop page:** redesigned confirmation messages to be contextual per product instead of a single global flash. This sidesteps the bug entirely for the page where rapid consecutive actions are possible, and as a side benefit fixed a related visibility problem; a global message at the top of a long, scrolled page was easy to miss.
- **Admin pages** (`admin_products.py`, `admin_import_csv.py`): kept `st.toast()`. Manual testing found the bug reproducible specifically when updating a product and then immediately deleting it via the adjacent "Update"/"Delete" buttons on the same "Edit / Delete" form, well within the toast's ~4-second window. Outside that specific adjacent-buttons case, normal pacing across other actions does not trigger it. Risk accepted: worst case is a missed confirmation message for the first of two rapid actions; both operations still complete correctly in the database regardless of what the toast displays — there is no data integrity impact.

**Known limitation, deferred:** a single, reliably auto-dismissing confirmation pattern usable everywhere (matching the original `st.toast()` intent without its reliability caveat) was not found within the timebox. Documented in `Architecture.md` (Design Decision #12) as a candidate future improvement.