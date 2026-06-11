# job-pdf-metadata-scrubber

CLI tool to scrub metadata from job application PDFs.

## Features
- Removes common PDF metadata like Author, Creator, Producer, and Title to ensure privacy.
- Uses `pypdf` or `PyPDF2` if available for robust metadata removal.
- Includes a regular expression fallback mechanism if no third-party PDF libraries are installed.

## Usage

```bash
python main.py input.pdf [output.pdf]
```

If `output.pdf` is not provided, the script will create a file named `input_clean.pdf` (or similar) in the same directory.

### Arguments

- `input_pdf`: Path to the input PDF file.
- `output_pdf`: (Optional) Path to save the scrubbed PDF file.

## Requirements

The script uses standard library packages by default. For more robust metadata removal, you can optionally install `pypdf` or `PyPDF2`:

```bash
pip install pypdf
# or
pip install PyPDF2
```
