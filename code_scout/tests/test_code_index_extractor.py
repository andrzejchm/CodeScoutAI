import json
import os

import pytest

from core.code_index.code_index_extractor import CodeIndexExtractor

TEST_FILES_DIR = "tests/test_source_files"


def get_test_cases():
    test_cases = []
    for filename in os.listdir(TEST_FILES_DIR):
        if not filename.endswith("_.json"):
            base_name = os.path.splitext(filename)[0]
            lang_file_path = os.path.join(TEST_FILES_DIR, filename)
            json_file_path = os.path.join(TEST_FILES_DIR, f"{base_name}_.json")

            if os.path.exists(json_file_path):
                with open(lang_file_path, "r") as f:
                    content = f.read()
                with open(json_file_path, "r") as f:
                    expected_symbols_data = json.load(f)

                expected_symbols = {
                    (s["name"], s["symbol_type"], s["start_line_number"], s["end_line_number"])
                    for s in expected_symbols_data
                }
                test_cases.append(pytest.param(lang_file_path, content, expected_symbols, id=f"test_{base_name}"))
    return test_cases


@pytest.mark.parametrize("file_path, content, expected_symbols", get_test_cases())
def test_extract_symbols_from_files(file_path, content, expected_symbols):
    extractor = CodeIndexExtractor()
    symbols = extractor.extract_symbols(file_path, content)

    actual_simplified = sorted(
        [(s.name, s.symbol_type, s.start_line_number, s.end_line_number) for s in symbols], key=lambda x: (x[2], x[0])
    )
    expected_simplified = sorted(
        list(expected_symbols),  # Convert set to list and sort directly
        key=lambda x: (x[2], x[0]),
    )

    if actual_simplified != expected_simplified:
        print(f"\n--- Mismatch for {file_path} ---")
        print(f"Expected ({len(expected_simplified)}) symbols")
        print(f"Actual ({len(actual_simplified)}) symbols")

        print("\n--- Actual Symbols ---")
        for item in actual_simplified:
            print(f"  {item}")

        print("\n--- Expected Symbols ---")
        for item in expected_simplified:
            print(f"  {item}")
        print("----------------------------------")

    assert actual_simplified == expected_simplified
