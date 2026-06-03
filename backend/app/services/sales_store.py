import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from app.config import get_settings


logger = logging.getLogger(__name__)


class SalesStoreError(Exception):
    pass


class SalesStore:
    def __init__(self, csv_path: Optional[str] = None) -> None:
        self._path = csv_path or get_settings().sales_data_path
        self._required_cols = [
            "date", "day_of_week", "week_number", "item", "unit",
            "quantity_sold", "unit_price_aud", "revenue_aud",
            "spoilage_days", "trend", "is_public_holiday", "is_pre_holiday",
        ]

    def _load(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self._path, parse_dates=["date"])
            return df
        except Exception as exc:
            logger.error("SalesStore: failed to load CSV: %s", exc)
            raise SalesStoreError(f"Cannot load sales data: {exc}") from exc

    def _save(self, df: pd.DataFrame) -> None:
        try:
            df.to_csv(self._path, index=False, date_format="%Y-%m-%d")
        except Exception as exc:
            logger.error("SalesStore: failed to save CSV: %s", exc)
            raise SalesStoreError(f"Cannot save sales data: {exc}") from exc

    def _infer_week_number(self, record_date: date, df: pd.DataFrame) -> int:
        if df.empty:
            return 1
        min_date = df["date"].min().date()
        delta_days = (record_date - min_date).days
        return (delta_days // 7) + 1

    def _infer_trend(self, item: str, current_weekly_qty: float, df: pd.DataFrame) -> str:
        item_df = df[df["item"] == item].copy()
        if item_df.empty or item_df["week_number"].nunique() < 2:
            return "stable"
        max_week = item_df["week_number"].max()
        prev_week_df = item_df[item_df["week_number"] == max_week - 1]
        if prev_week_df.empty:
            return "stable"
        prev_total = prev_week_df["quantity_sold"].sum()
        if prev_total == 0:
            return "stable"
        pct = (current_weekly_qty - prev_total) / prev_total * 100
        if pct > 5:
            return "rising"
        if pct < -5:
            return "declining"
        return "stable"

    def get_items(self) -> List[Dict[str, Any]]:
        df = self._load()
        items = (
            df.groupby("item")
            .agg(
                unit=("unit", "first"),
                unit_price_aud=("unit_price_aud", "mean"),
                spoilage_days=("spoilage_days", "first"),
            )
            .reset_index()
        )
        return [
            {
                "item": row["item"],
                "unit": row["unit"],
                "unit_price_aud": round(float(row["unit_price_aud"]), 2),
                "spoilage_days": int(row["spoilage_days"]),
            }
            for _, row in items.iterrows()
        ]

    def append_daily_sales(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0

        df = self._load()

        new_rows = []
        for rec in records:
            record_date = rec.get("date")
            if isinstance(record_date, str):
                record_date = datetime.strptime(record_date, "%Y-%m-%d").date()

            item = str(rec["item"])
            qty = float(rec["quantity_sold"])
            unit_price = float(rec.get("unit_price_aud", 0.0))
            revenue = round(qty * unit_price, 2)
            week_num = self._infer_week_number(record_date, df)
            day_name = record_date.strftime("%A")

            # Get metadata from existing rows for this item
            item_rows = df[df["item"] == item]
            unit = str(item_rows["unit"].iloc[0]) if not item_rows.empty else rec.get("unit", "unit")
            spoilage_days = int(item_rows["spoilage_days"].iloc[0]) if not item_rows.empty else int(rec.get("spoilage_days", 7))

            # Check for duplicate (same date + item)
            dupe = df[
                (df["date"].dt.date == record_date) & (df["item"] == item)
            ]
            if not dupe.empty:
                logger.info("Skipping duplicate: %s on %s", item, record_date)
                continue

            # Infer trend from existing weekly totals
            current_week_df = df[df["week_number"] == week_num]
            current_weekly_qty = current_week_df[current_week_df["item"] == item]["quantity_sold"].sum() + qty
            trend = self._infer_trend(item, current_weekly_qty, df)

            new_rows.append({
                "date": record_date.strftime("%Y-%m-%d"),
                "day_of_week": day_name,
                "week_number": week_num,
                "item": item,
                "unit": unit,
                "quantity_sold": qty,
                "unit_price_aud": unit_price,
                "revenue_aud": revenue,
                "spoilage_days": spoilage_days,
                "trend": trend,
                "is_public_holiday": int(rec.get("is_public_holiday", 0)),
                "is_pre_holiday": int(rec.get("is_pre_holiday", 0)),
            })

        if not new_rows:
            logger.info("SalesStore: no new rows to append (all duplicates)")
            return 0

        new_df = pd.DataFrame(new_rows)
        combined = pd.concat([df, new_df], ignore_index=True)
        combined = combined.sort_values(["date", "item"]).reset_index(drop=True)
        self._save(combined)
        logger.info("SalesStore: appended %d new rows", len(new_rows))
        return len(new_rows)

    def get_latest_week_number(self) -> int:
        df = self._load()
        if df.empty:
            return 0
        return int(df["week_number"].max())

    def get_weeks_of_data(self) -> int:
        df = self._load()
        if df.empty:
            return 0
        return int(df["week_number"].nunique())

    def generate_template_csv(self) -> str:
        items = self.get_items()
        item_names = [i["item"] for i in items]
        header = "Date," + ",".join(item_names)
        example_row = "2026-06-10," + ",".join(["0"] * len(item_names))
        lines = [
            "# MarketMate Daily Sales Template",
            "# Fill in the quantity sold for each item on each day.",
            "# Leave as 0 or blank if an item was not sold that day.",
            "# Date format: YYYY-MM-DD or DD/MM/YYYY",
            header,
            example_row,
        ]
        return "\n".join(lines)

    def parse_upload_file(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        import io
        ext = filename.lower().rsplit(".", 1)[-1]

        try:
            if ext in ("xlsx", "xls"):
                engine = "openpyxl" if ext == "xlsx" else "xlrd"
                raw = pd.read_excel(io.BytesIO(content), engine=engine, header=None)
            else:
                # CSV - skip comment lines starting with #
                text = content.decode("utf-8-sig")
                non_comment = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
                raw = pd.read_csv(io.StringIO(non_comment), header=None)
        except Exception as exc:
            raise SalesStoreError(f"Cannot parse file '{filename}': {exc}") from exc

        if raw.empty:
            raise SalesStoreError("File is empty.")

        # Find header row - first row with non-numeric first cell
        header_row = 0
        for i, row in raw.iterrows():
            first_cell = str(row.iloc[0]).strip().lower()
            if first_cell in ("date", "day", "dates") or "/" in first_cell or "-" in first_cell:
                try:
                    pd.to_datetime(first_cell, dayfirst=True)
                    # It parsed as a date, so row 0 is data, not header
                    header_row = None
                    break
                except Exception:
                    header_row = int(i)
                    break

        if header_row is not None:
            raw.columns = raw.iloc[header_row]
            raw = raw.iloc[header_row + 1:].reset_index(drop=True)
            raw.columns = [str(c).strip() for c in raw.columns]

        raw = raw.dropna(how="all")

        cols_lower = [c.lower() for c in raw.columns]

        # Detect format: long if has 'item' and ('quantity_sold' or 'qty' or 'quantity')
        is_long = "item" in cols_lower and any(
            kw in cols_lower for kw in ("quantity_sold", "qty", "quantity")
        )

        if is_long:
            return self._parse_long_format(raw)
        else:
            return self._parse_wide_format(raw)

    def _parse_long_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        col_map = {c.lower(): c for c in df.columns}
        date_col = col_map.get("date", col_map.get("day", list(col_map.values())[0]))
        item_col = col_map.get("item", col_map.get("items", "item"))
        qty_col = col_map.get("quantity_sold", col_map.get("qty", col_map.get("quantity", "quantity_sold")))
        price_col = col_map.get("unit_price_aud", col_map.get("price", col_map.get("unit_price", None)))

        records = []
        for _, row in df.iterrows():
            try:
                raw_date = str(row[date_col]).strip()
                parsed_date = pd.to_datetime(raw_date, dayfirst=True).strftime("%Y-%m-%d")
                item = str(row[item_col]).strip()
                qty = float(str(row[qty_col]).replace(",", "").strip())
                if qty <= 0 or not item or item.lower() in ("nan", "none", ""):
                    continue
                rec: Dict[str, Any] = {"item": item, "quantity_sold": qty, "date": parsed_date}
                if price_col and price_col in row.index:
                    try:
                        rec["unit_price_aud"] = float(str(row[price_col]).replace(",", ""))
                    except Exception:
                        pass
                records.append(rec)
            except Exception:
                continue
        return records

    def _parse_wide_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        # First column = date, remaining = item names
        date_col = df.columns[0]
        item_cols = [c for c in df.columns[1:] if str(c).strip() and str(c).lower() not in ("nan", "none", "")]

        # Get unit prices from existing data for price lookup
        existing = self._load()
        price_map: Dict[str, float] = {}
        if not existing.empty:
            for item in existing["item"].unique():
                rows = existing[existing["item"] == item]
                price_map[item.lower()] = float(rows["unit_price_aud"].mean())

        records = []
        for _, row in df.iterrows():
            try:
                raw_date = str(row[date_col]).strip()
                if not raw_date or raw_date.lower() in ("nan", "none", "date"):
                    continue
                parsed_date = pd.to_datetime(raw_date, dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                continue

            for item_col in item_cols:
                try:
                    val = row[item_col]
                    if pd.isna(val) or str(val).strip() in ("", "0", "0.0", "nan"):
                        continue
                    qty = float(str(val).replace(",", "").strip())
                    if qty <= 0:
                        continue
                    item_name = str(item_col).strip()
                    rec: Dict[str, Any] = {
                        "item": item_name,
                        "quantity_sold": qty,
                        "date": parsed_date,
                    }
                    if item_name.lower() in price_map:
                        rec["unit_price_aud"] = price_map[item_name.lower()]
                    records.append(rec)
                except Exception:
                    continue
        return records


_sales_store: Optional[SalesStore] = None


def get_sales_store() -> SalesStore:
    global _sales_store
    if _sales_store is None:
        _sales_store = SalesStore()
    return _sales_store
