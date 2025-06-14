import pytest

from utils import (
    _to_roman,
    apply_legal_numbering,
    format_legal_list,
    format_signature_block,
    format_annex_reference,
    create_document_footer,
    create_document_header,
    create_table_of_contents,
    split_into_pages,
    add_page_numbers,
    format_party_designation,
    create_letterhead_from_template,
    create_formatted_docx,
)


def test_formatter_imports():
    funcs = [
        _to_roman,
        apply_legal_numbering,
        format_legal_list,
        format_signature_block,
        format_annex_reference,
        create_document_footer,
        create_document_header,
        create_table_of_contents,
        split_into_pages,
        add_page_numbers,
        format_party_designation,
        create_letterhead_from_template,
        create_formatted_docx,
    ]
    for f in funcs:
        assert callable(f)
