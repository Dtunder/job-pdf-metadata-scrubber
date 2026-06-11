# job-pdf-metadata-scrubber

[![Tests Status](https://img.shields.io/badge/tests-passing-brightgreen)](#)

CLI tool to scrub metadata from job application PDFs.

## Features
- Removes common PDF metadata like Author, Creator, Producer, and Title to ensure privacy.
- Uses `pypdf` or `PyPDF2` if available for robust metadata removal.
- Includes a regular expression fallback mechanism if no third-party PDF libraries are installed.

## Setup and Configuration

### Environment
The script uses standard Python libraries by default. For the most robust metadata removal, it is recommended to install either `pypdf` or `PyPDF2` in your environment:

```bash
pip install pypdf
# or
pip install PyPDF2
```

### Logging Configuration
The tool uses standard Python `logging` to provide structured output. By default, it is configured to print `INFO` level and above to the console with the format:
`%(asctime)s - %(levelname)s - %(message)s`

You can modify the `logging.basicConfig()` call at the top of `main.py` if you require different logging levels or log files.

## CLI Instructions

Use the command line to process your PDF files:

```bash
python main.py <input.pdf> [output.pdf]
```

### Examples
- **Basic Usage:** Provide just the input file. The tool will generate a cleaned version with `_clean` appended to the filename.
  ```bash
  python main.py resume.pdf
  ```
  *(Creates `resume_clean.pdf` in the same directory)*

- **Specify Output Path:** Provide both input and output paths.
  ```bash
  python main.py resume.pdf ./scrubbed/resume_final.pdf
  ```

### CLI Arguments
- `input_pdf`: (Required) Path to the input PDF file. The file must exist and be readable.
- `output_pdf`: (Optional) Path to save the scrubbed PDF file. If omitted, defaults to `<input_basename>_clean.pdf`.

## API Reference Documentation

You can also import functions from `main.py` directly into your own Python scripts.

### `try_import_pypdf()`
Attempt to import a PDF library (pypdf, PyPDF2, or pdfplumber).
- **Returns:** A tuple containing the imported module object and its name as a string (e.g., `(module, "pypdf")`). If no library can be imported, returns `(None, None)`.

### `validate_paths(input_path, output_path)`
Validate the given input and output paths.
- **Args:**
  - `input_path` (str): The path to the input file.
  - `output_path` (str): The path to the output file.
- **Raises:**
  - `TypeError`: If either input_path or output_path is not a string.
  - `ValueError`: If either path is empty or consists only of whitespace.
  - `ValueError`: If the absolute paths of input and output are identical.

### `scrub_with_pypdf(pdf_lib, lib_name, input_path, output_path)`
Scrub metadata from a PDF file using pypdf or PyPDF2.
- **Args:**
  - `pdf_lib` (module): The imported PDF library module (e.g., pypdf).
  - `lib_name` (str): The name of the library (e.g., "pypdf", "PyPDF2").
  - `input_path` (str): Path to the input PDF file.
  - `output_path` (str): Path where the cleaned PDF will be saved.
- **Returns:** `bool` - True if scrubbing was successful, False otherwise.

### `scrub_with_regex(input_path, output_path)`
Scrub metadata from a PDF file using regular expressions. This acts as a fallback when no suitable PDF library is available for writing.
- **Args:**
  - `input_path` (str): Path to the input PDF file.
  - `output_path` (str): Path where the cleaned PDF will be saved.
- **Returns:** `bool` - True if scrubbing was successful, False otherwise.
