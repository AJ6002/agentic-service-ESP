"""
Docling Advanced Document Parser Integration for ESP Knowledge Base
Uses IBM Docling (docling) for AI-powered layout analysis, high-fidelity table extraction,
and markdown conversion.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ESPDoclingParser:
    """
    Wrapper for Docling DocumentConverter to parse engineering PDFs, DOCX, and standards
    into layout-aware Markdown and structured JSON.
    """

    def __init__(self, export_markdown: bool = True, export_json: bool = True):
        self.export_markdown = export_markdown
        self.export_json = export_json
        self._converter = None

    def _init_converter(self):
        """Lazy load Docling DocumentConverter"""
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized successfully.")
            except ImportError as e:
                logger.error("Docling package not yet available. Run 'pip install docling'.")
                raise RuntimeError("Docling is not installed in the environment.") from e

    def parse_document(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Parse an input document using Docling and save outputs.

        Args:
            input_path: Path to the document (PDF, DOCX, etc.)
            output_dir: Path where output markdown/JSON will be written

        Returns:
            Dict containing metadata and output file paths.
        """
        self._init_converter()

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        logger.info(f"Parsing document with Docling: {input_path}")
        result = self._converter.convert(input_path)
        doc = result.document

        markdown_path = os.path.join(output_dir, f"{base_name}.md")
        json_path = os.path.join(output_dir, f"{base_name}_docling.json")

        md_content = doc.export_to_markdown()
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        doc_dict = doc.export_to_dict()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)

        return {
            "status": "SUCCESS",
            "input_file": input_path,
            "markdown_output": markdown_path,
            "json_output": json_path,
            "char_count": len(md_content),
            "tables_extracted": len(getattr(doc, "tables", []))
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        parser = ESPDoclingParser()
        res = parser.parse_document(sys.argv[1], sys.argv[2])
        print(json.dumps(res, indent=2))
