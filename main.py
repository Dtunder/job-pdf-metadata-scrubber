import argparse
import logging
import os
import re
import sys
from typing import Any, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def try_import_pypdf() -> Tuple[Optional[Any], Optional[str]]:
    """Attempt to import a PDF library (pypdf, PyPDF2, or pdfplumber).

    This function attempts to load supported PDF libraries in a specific
    order of preference: pypdf, PyPDF2, and finally pdfplumber.

    Returns:
        tuple: A tuple containing the imported module object and its
            name as a string (e.g., (module, "pypdf")). If no library
            can be imported, returns (None, None).
    """
    try:
        import pypdf

        return pypdf, "pypdf"
    except ImportError:
        pass

    try:
        import PyPDF2

        return PyPDF2, "PyPDF2"
    except ImportError:
        pass

    try:
        import pdfplumber

        return pdfplumber, "pdfplumber"
    except ImportError:
        pass

    return None, None


def validate_paths(input_path: str, output_path: str) -> None:
    """Validate the given input and output paths.

    Args:
        input_path (str): The path to the input file.
        output_path (str): The path to the output file.

    Raises:
        TypeError: If either input_path or output_path is not a string.
        ValueError: If either path is empty or consists only of whitespace.
        ValueError: If the absolute paths of input and output are identical.
    """
    if not isinstance(input_path, str) or not isinstance(output_path, str):
        raise TypeError("Input and output paths must be strings.")
    if not input_path.strip() or not output_path.strip():
        raise ValueError("Input and output paths cannot be empty.")
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("Input and output paths cannot be identical.")


def scrub_with_pypdf(
    pdf_lib: Any, lib_name: str, input_path: str, output_path: str
) -> bool:
    """Scrub metadata from a PDF file using pypdf or PyPDF2.

    This function reads a PDF, removes common metadata fields (Author,
    Creator, Producer, Title), and writes the cleaned PDF to the output path.
    It uses an optimized approach with `append_pages_from_reader`.

    Args:
        pdf_lib (module): The imported PDF library module (e.g., pypdf).
        lib_name (str): The name of the library (e.g., "pypdf", "PyPDF2").
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the cleaned PDF will be saved.

    Returns:
        bool: True if scrubbing was successful, False otherwise.
    """
    try:
        validate_paths(input_path, output_path)
    except (TypeError, ValueError) as e:
        logger.error(f"Validation Error: {e}")
        return False

    if lib_name == "pdfplumber":
        logger.warning(
            "pdfplumber found but writing requires pypdf/PyPDF2. Falling back to regex."
        )
        return False

    try:
        reader = pdf_lib.PdfReader(input_path)
        writer = pdf_lib.PdfWriter()

        # Optimize: Bulk append pages from the reader
        writer.append_pages_from_reader(reader)

        writer.add_metadata(
            {"/Author": "", "/Creator": "", "/Producer": "", "/Title": ""}
        )

        with open(output_path, "wb") as f:
            writer.write(f)
        return True
    except FileNotFoundError:
        logger.error(f"Error using {lib_name}: File not found '{input_path}'")
        return False
    except PermissionError:
        logger.error(
            f"Error using {lib_name}: Permission denied when accessing '{input_path}' or '{output_path}'"
        )
        return False
    except OSError as e:
        logger.error(f"Error using {lib_name}: OS error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Error using {lib_name}: {e}")
        return False


def scrub_with_regex(input_path: str, output_path: str) -> bool:
    """Scrub metadata from a PDF file using regular expressions.

    This acts as a fallback when no suitable PDF library is available for
    writing. It reads the raw binary data of the PDF, finds common metadata
    tags using regex, and clears their values.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the cleaned PDF will be saved.

    Returns:
        bool: True if scrubbing was successful, False otherwise.
    """
    try:
        validate_paths(input_path, output_path)
    except (TypeError, ValueError) as e:
        logger.error(f"Validation Error: {e}")
        return False

    try:
        with open(input_path, "rb") as f:
            data = f.read()

        # Combine tags into a single pattern to avoid multiple passes over the string
        # Match /Tag (value) handling escaped characters inside
        # In PDF, strings in parentheses can contain escaped parens \( or \).
        pattern_str = (
            rb"/(Author|Creator|Producer|Title)\s*\((?:[^()\\]|\\.)*\)"
        )
        data = re.sub(pattern_str, rb"/\1 ()", data)

        # PDF hex string format: /Tag <hex_value>
        pattern_hex = rb"/(Author|Creator|Producer|Title)\s*<[0-9a-fA-F]*>"
        data = re.sub(pattern_hex, rb"/\1 <>", data)

        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except FileNotFoundError:
        logger.error(
            f"Error using regex fallback: File not found '{input_path}'"
        )
        return False
    except PermissionError:
        logger.error(
            f"Error using regex fallback: Permission denied when accessing '{input_path}' or '{output_path}'"
        )
        return False
    except OSError as e:
        logger.error(f"Error using regex fallback: OS error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Error using regex fallback: {e}")
        return False


def main() -> None:
    """Main entry point for the CLI tool.

    Parses command-line arguments, validates file paths and permissions,
    determines the best available method for metadata scrubbing (PDF library
    vs. regex fallback), and executes the scrubbing process.
    """
    parser = argparse.ArgumentParser(
        description="Scrub metadata (Author, Creator, Producer, Title) from a PDF file."
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument(
        "output_pdf", nargs="?", help="Path to the output PDF file (optional)"
    )

    args = parser.parse_args()

    input_path = args.input_pdf
    if not os.path.isfile(input_path):
        logger.error(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    if not os.access(input_path, os.R_OK):
        logger.error(f"Error: Input file '{input_path}' is not readable.")
        sys.exit(1)

    output_path = args.output_pdf
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        logger.error(
            "Error: Input and output paths cannot be identical to prevent data loss."
        )
        sys.exit(1)

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir and not os.path.isdir(output_dir):
        logger.error(f"Error: Output directory '{output_dir}' does not exist.")
        sys.exit(1)

    logger.info(f"Processing '{input_path}' -> '{output_path}'")

    pdf_lib, lib_name = try_import_pypdf()
    success = False

    if pdf_lib and lib_name in ["pypdf", "PyPDF2"]:
        logger.info(f"Using {lib_name} for metadata scrubbing...")
        success = scrub_with_pypdf(pdf_lib, lib_name, input_path, output_path)

    if not success:
        logger.info("Using regex fallback for metadata scrubbing...")
        success = scrub_with_regex(input_path, output_path)

    if success:
        logger.info("Metadata successfully scrubbed!")
    else:
        logger.error("Failed to scrub metadata.")
        sys.exit(1)


if __name__ == "__main__":
    main()
