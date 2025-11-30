import logging
import os
import tempfile

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from flamapy.metamodels.fm_metamodel.transformations import GlencoeWriter, SPLOTWriter, UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import DimacsWriter, FmToPysat
from flask import jsonify, send_file
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser

from app.modules.flamapy import flamapy_bp
from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


@flamapy_bp.route("/flamapy/check_csv/<int:file_id>", methods=["GET"])
def check_csv(file_id):
    """
    Validate CSV file format and structure.
    Checks for:
    - Valid CSV syntax
    - Consistent number of columns
    - Proper delimiter usage
    - Encoding issues
    """
    import csv
    from io import StringIO
    
    try:
        hubfile = HubfileService().get_by_id(file_id)
        file_path = hubfile.get_path()
        
        errors = []
        warnings = []
        
        # Try to read the file with different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            errors.append("Unable to read file with common encodings (UTF-8, Latin-1, ISO-8859-1)")
            return jsonify({"errors": errors}), 400
        
        # Detect delimiter
        sniffer = csv.Sniffer()
        try:
            sample = content[:1024]  # Use first 1KB for detection
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            # Default to comma if detection fails
            delimiter = ','
            warnings.append(f"Could not detect delimiter automatically, assuming comma (,)")
        
        # Parse CSV
        lines = content.split('\n')
        reader = csv.reader(StringIO(content), delimiter=delimiter)
        
        rows = list(reader)
        if not rows:
            errors.append("File is empty")
            return jsonify({"errors": errors}), 400
        
        # Check for consistent column count
        non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
        if not non_empty_rows:
            errors.append("File contains no data")
            return jsonify({"errors": errors}), 400
        
        expected_cols = len(non_empty_rows[0])
        for i, row in enumerate(non_empty_rows[1:], start=2):
            if len(row) != expected_cols:
                errors.append(f"Line {i}: Expected {expected_cols} columns, found {len(row)}")
        
        if errors:
            return jsonify({"errors": errors, "warnings": warnings}), 400
        
        # Success response with file info
        response_data = {
            "message": "Valid CSV file",
            "rows": len(non_empty_rows),
            "columns": expected_cols,
            "delimiter": delimiter,
            "encoding": used_encoding
        }
        
        if warnings:
            response_data["warnings"] = warnings
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.exception(f"Error validating CSV file {file_id}")
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route("/flamapy/check_uvl/<int:file_id>", methods=["GET"])
def check_uvl(file_id):
    """Legacy endpoint for UVL validation - no longer used for CSV-only datasets"""
    class CustomErrorListener(ErrorListener):
        def __init__(self):
            self.errors = []

        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            if "\\t" in msg:
                warning_message = (
                    f"The UVL has the following warning that prevents reading it: " f"Line {line}:{column} - {msg}"
                )
                print(warning_message)
                self.errors.append(warning_message)
            else:
                error_message = (
                    f"The UVL has the following error that prevents reading it: " f"Line {line}:{column} - {msg}"
                )
                self.errors.append(error_message)

    try:
        hubfile = HubfileService().get_by_id(file_id)
        input_stream = FileStream(hubfile.get_path())
        lexer = UVLCustomLexer(input_stream)

        error_listener = CustomErrorListener()

        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)

        stream = CommonTokenStream(lexer)
        parser = UVLPythonParser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)

        # tree = parser.featureModel()

        if error_listener.errors:
            return jsonify({"errors": error_listener.errors}), 400

        # Optional: Print the parse tree
        # print(tree.toStringTree(recog=parser))

        return jsonify({"message": "Valid Model"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route("/flamapy/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


@flamapy_bp.route("/flamapy/to_glencoe/<int:file_id>", methods=["GET"])
def to_glencoe(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    try:
        hubfile = HubfileService().get_or_404(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        GlencoeWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_glencoe.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route("/flamapy/to_splot/<int:file_id>", methods=["GET"])
def to_splot(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".splx", delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        SPLOTWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_splot.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route("/flamapy/to_cnf/<int:file_id>", methods=["GET"])
def to_cnf(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".cnf", delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        sat = FmToPysat(fm).transform()
        DimacsWriter(temp_file.name, sat).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_cnf.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)
