import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.ingestion import run_ingestion


SAMPLE_CSV_CONTENT = """date,day_of_week,week_number,item,unit,quantity_sold,unit_price_aud,revenue_aud,spoilage_days,trend,is_public_holiday,is_pre_holiday
2026-04-01,Wednesday,1,Bananas,kg,166.7,2.99,498.43,7,stable,0,0
2026-04-01,Wednesday,1,Strawberries,punnet,167.7,3.99,669.12,3,declining,0,0
2026-04-02,Thursday,1,Bananas,kg,245.1,2.99,732.85,7,stable,0,1
2026-04-02,Thursday,1,Strawberries,punnet,269.0,3.99,1073.31,3,declining,0,1
2026-04-08,Wednesday,2,Bananas,kg,155.0,2.99,463.45,7,stable,0,0
2026-04-08,Wednesday,2,Strawberries,punnet,120.0,3.99,478.8,3,declining,0,0
"""


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_sales.csv"
    csv_file.write_text(SAMPLE_CSV_CONTENT)
    return str(csv_file)


def test_run_ingestion_returns_document_count(sample_csv):
    mock_vs = MagicMock()
    mock_vs.document_count.return_value = 0
    count = run_ingestion(mock_vs, sample_csv)
    assert count > 0
    mock_vs.add_documents.assert_called_once()


def test_run_ingestion_calls_add_documents_with_correct_structure(sample_csv):
    mock_vs = MagicMock()
    run_ingestion(mock_vs, sample_csv)
    call_args = mock_vs.add_documents.call_args[0][0]
    assert isinstance(call_args, list)
    assert len(call_args) > 0

    first_doc = call_args[0]
    assert "id" in first_doc
    assert "text" in first_doc
    assert "metadata" in first_doc


def test_run_ingestion_document_text_format(sample_csv):
    mock_vs = MagicMock()
    run_ingestion(mock_vs, sample_csv)
    docs = mock_vs.add_documents.call_args[0][0]

    banana_docs = [d for d in docs if "Bananas" in d["text"]]
    assert len(banana_docs) > 0
    text = banana_docs[0]["text"]
    assert "Week" in text
    assert "Bananas" in text
    assert "Revenue" in text


def test_run_ingestion_metadata_fields(sample_csv):
    mock_vs = MagicMock()
    run_ingestion(mock_vs, sample_csv)
    docs = mock_vs.add_documents.call_args[0][0]

    for doc in docs:
        meta = doc["metadata"]
        assert "week_number" in meta
        assert "item" in meta
        assert "unit" in meta
        assert "spoilage_days" in meta
        assert "trend" in meta
        assert "total_qty" in meta
        assert "revenue" in meta


def test_run_ingestion_missing_file():
    mock_vs = MagicMock()
    with pytest.raises(Exception):
        run_ingestion(mock_vs, "/nonexistent/path/sales.csv")
