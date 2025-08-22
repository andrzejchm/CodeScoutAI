"""
This module contains tree-sitter queries for extracting code symbols from various languages.
The queries are designed to be executed by the SymbolExtractor.
"""

# A mapping from language identifiers to their specific queries.
QUERIES = {
    "python": r"""
        (class_definition name: (identifier) @class.name) @class.definition
        (function_definition name: (identifier) @function.name) @function.definition
    """,
    "javascript": r"""
        (class_declaration name: (identifier) @class.name) @class.definition
        (function_declaration name: (identifier) @function.name) @function.definition
        (method_definition name: (property_identifier) @method.name) @method.definition
    """,
    "typescript": r"""
        (class_declaration name: (type_identifier) @class.name) @class.definition
        (method_signature name: (property_identifier) @method.name) @method.definition
        (method_definition name: (property_identifier) @method.name) @method.definition
        (public_field_definition name: (property_identifier) @field.name) @field.definition
        (property_signature name: (property_identifier) @field.name) @field.definition
    """,
    "dart": r"""
        (class_definition (identifier) @class.name) @class.definition
        (mixin_declaration  (identifier) @mixin.name) @mixin.definition
        (enum_declaration  (identifier) @enum.name) @enum.definition
    """,
}
