from core.code_index.code_index_extractor import CodeIndexExtractor


def test_extract_python_symbols():
    extractor = CodeIndexExtractor()
    content = """
class MyClass:
    def my_method(self):
        pass

def my_function():
    pass
"""
    file_path = "test.py"
    symbols = extractor.extract_symbols(file_path, content)

    assert len(symbols) == 3

    simplified_symbols = {(s.name, s.symbol_type, s.start_line_number, s.end_line_number) for s in symbols}

    assert ("MyClass", "class", 2, 4) in simplified_symbols
    assert ("my_method", "function", 3, 4) in simplified_symbols
    assert ("my_function", "function", 6, 7) in simplified_symbols


def test_extract_javascript_symbols():
    extractor = CodeIndexExtractor()
    content = """
class MyClass {
  myMethod() {
  }
}

function myFunction() {
}

const myArrowFunction = () => {
};
"""
    file_path = "test.js"
    symbols = extractor.extract_symbols(file_path, content)

    simplified_symbols = {(s.name, s.symbol_type, s.start_line_number, s.end_line_number) for s in symbols}

    assert len(symbols) == 4
    assert ("MyClass", "class", 2, 5) in simplified_symbols
    assert ("myMethod", "method", 3, 4) in simplified_symbols
    assert ("myFunction", "function", 7, 8) in simplified_symbols
    assert ("myArrowFunction", "function", 10, 11) in simplified_symbols


def test_extract_dart_symbols():
    extractor = CodeIndexExtractor()
    content = """
class MyClass {
  void myMethod() {
  }
}
"""
    file_path = "test.dart"
    symbols = extractor.extract_symbols(file_path, content)

    simplified_symbols = {(s.name, s.symbol_type, s.start_line_number, s.end_line_number) for s in symbols}

    assert len(symbols) == 2
    assert ("MyClass", "class", 2, 5) in simplified_symbols
    assert ("myMethod", "method", 3, 3) in simplified_symbols
