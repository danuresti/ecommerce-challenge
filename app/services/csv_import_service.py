import logging
import pandas as pd
from dataclasses import dataclass, field
from app.services.product_service import ProductService
from app.core.exceptions import ValidationError, DuplicateError

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    total_rows: int = 0
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


class CsvImportService:
    REQUIRED_COLUMNS = {"name", "sku", "description", "category", "price", "stock", "weight_kg"}

    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def import_from_csv(self, file_path: str) -> ImportResult:
        result = ImportResult()
        df = pd.read_csv(file_path)

        missing_columns = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            raise ValidationError(f"CSV is missing required columns: {', '.join(missing_columns)}")

        result.total_rows = len(df)

        for index, row in df.iterrows():
            csv_line = index + 2

            if self._is_blank_row(row):
                result.skipped += 1
                result.errors.append(f"Row {csv_line}: empty row, skipped.")
                continue

            try:
                data = self._row_to_dict(row)
                self.product_service.create_product(data)
                result.imported += 1
            except (ValidationError, DuplicateError) as e:
                result.skipped += 1
                result.errors.append(f"Row {csv_line}: {e}")
            except (ValueError, TypeError) as e:
                result.skipped += 1
                result.errors.append(f"Row {csv_line}: malformed data ({e})")

        logger.info(
            f"CSV import completed: file={file_path}, total_rows={result.total_rows}, "
            f"imported={result.imported}, skipped={result.skipped}"
        )
        if result.skipped > 0:
            logger.warning(f"CSV import had {result.skipped} skipped row(s): file={file_path}")

        return result

    def _is_blank_row(self, row: pd.Series) -> bool:
        return row.drop(labels=["weight_kg"], errors="ignore").isna().all()

    def _row_to_dict(self, row: pd.Series) -> dict:
        weight = row.get("weight_kg")
        return {
            "name": self._clean_text(row.get("name")),
            "sku": self._clean_text(row.get("sku")),
            "description": self._clean_text(row.get("description")),
            "category": self._clean_text(row.get("category")),
            "price": self._clean_price(row["price"]),
            "stock": int(row["stock"]),
            "weight_kg": float(weight) if pd.notna(weight) else None,
        }

    def _clean_text(self, value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _clean_price(self, value) -> float:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        return float(value)