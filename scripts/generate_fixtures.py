from pathlib import Path

import pandas as pd


def create_fixtures():
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 1. valid.csv
    valid_data = pd.DataFrame(
        {
            "Keyword": ["seo optimization", "content marketing", "digital strategy"],
            "volume": [1000, 500, 300],
            "cpc": [2.5, 1.2, 3.0],
        }
    )
    valid_data.to_csv(fixtures_dir / "valid.csv", index=False)

    # 2. valid.xlsx
    valid_data.to_excel(fixtures_dir / "valid.xlsx", index=False)

    # 3. missing_column.csv (no 'keyword' or aliases)
    missing_data = pd.DataFrame({"volume": [1000, 500], "cpc": [2.5, 1.2]})
    missing_data.to_csv(fixtures_dir / "missing_column.csv", index=False)

    # 4. empty.csv
    empty_data = pd.DataFrame(columns=["keyword", "volume"])
    empty_data.to_csv(fixtures_dir / "empty.csv", index=False)

    # 5. duplicate_rows.csv
    duplicate_data = pd.DataFrame(
        {
            "keyword": ["seo", "seo", "content", "content", "SEO"],
            "volume": [100, 100, 200, 200, 100],
        }
    )
    duplicate_data.to_csv(fixtures_dir / "duplicate_rows.csv", index=False)

    # 6. unicode.csv
    unicode_data = pd.DataFrame(
        {
            "Search Keyword": ["optimización seo \u2728", "マーケティング", "café"],
            "volume": [500, 1000, 200],
        }
    )
    # Save as UTF-8
    unicode_data.to_csv(fixtures_dir / "unicode.csv", index=False, encoding="utf-8")

    # 7. invalid_extension.txt
    with open(fixtures_dir / "invalid_extension.txt", "w") as f:
        f.write("keyword,volume\nseo,100")

    # 8. malformed.csv (we'll just write bad string directly)
    with open(fixtures_dir / "malformed.csv", "w") as f:
        f.write('keyword,volume\n"unclosed quote,100\nnormal,200\n')

    print("Fixtures generated successfully.")


if __name__ == "__main__":
    create_fixtures()
