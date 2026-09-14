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
