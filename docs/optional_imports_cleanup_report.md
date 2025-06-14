# Optional Imports Cleanup Report

The following files had conditional imports and availability flags removed. All imports are now standard and fallback paths were eliminated:

- `managers/company_info_manager.py`
- `managers/azure_blob_manager.py`
- `managers/azure_search_manager.py`
- `managers/export_manager.py`
- `managers/multi_llm_manager.py`
- `managers/llm_manager.py`
- `modules/comparison.py`
- `modules/mapping.py`
- `modules/timeline.py`
- `modules/redaction2.py`
- `modules/template.py`
- `modules/explorer.py`
- `modules/email.py`

All code now assumes the required third‑party libraries are installed.
