"""Tests for the InputLoader."""

import io

import pandas as pd
import pytest

from keyword_intelligence.input_loader.exceptions import (
    EmptyFileError,
    MissingSheetError,
    UnsupportedFileFormatError,
)
from keyword_intelligence.input_loader.loader import InputLoader


@pytest.fixture
def loader():
    return InputLoader()


def test_load_csv_success(loader, tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("keyword,volume\nlenovo laptop,100")

    df = loader.load(csv_file)
    assert not df.empty
    assert len(df) == 1
    assert "keyword" in df.columns


def test_load_csv_empty(loader, tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("")

    with pytest.raises(EmptyFileError):
        loader.load(csv_file)


def test_load_unsupported_extension(loader, tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("keyword\nlenovo laptop")

    with pytest.raises(UnsupportedFileFormatError):
        loader.load(txt_file)


def test_load_excel_success(loader, tmp_path):
    excel_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"keyword": ["laptop"], "volume": [100]})

    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
        df.to_excel(writer, sheet_name="Sheet2", index=False)

    loaded_df = loader.load(excel_file)
    assert not loaded_df.empty

    loaded_df_2 = loader.load(excel_file, sheet_name="Sheet2")
    assert not loaded_df_2.empty


def test_load_excel_missing_sheet(loader, tmp_path):
    excel_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"keyword": ["laptop"]})

    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

    with pytest.raises(MissingSheetError):
        loader.load(excel_file, sheet_name="NonExistentSheet")


def test_load_excel_bytes_success(loader):
    df = pd.DataFrame({"keyword": ["laptop"]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

    raw_bytes = buf.getvalue()

    loaded_df = loader.load(raw_bytes, file_name="test.xlsx")
    assert not loaded_df.empty
    assert loaded_df.iloc[0]["keyword"] == "laptop"


def test_extract_sheet_names(loader, tmp_path):
    excel_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"keyword": ["laptop"]})

    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name="Data1", index=False)
        df.to_excel(writer, sheet_name="Data2", index=False)

    sheets = loader.get_sheet_names(excel_file)
    assert sheets == ["Data1", "Data2"]
