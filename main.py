import argparse
import sys
import os
import re

def try_import_pypdf():
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

def scrub_with_pypdf(pdf_lib, lib_name, input_path, output_path):
    if lib_name == "pdfplumber":
        print("pdfplumber found but writing requires pypdf/PyPDF2. Falling back to regex.")
        return False

    try:
        reader = pdf_lib.PdfReader(input_path)
        writer = pdf_lib.PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata({
            "/Author": "",
            "/Creator": "",
            "/Producer": "",
            "/Title": ""
        })

        with open(output_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"Error using {lib_name}: {e}")
        return False

def scrub_with_regex(input_path, output_path):
    try:
        with open(input_path, "rb") as f:
            data = f.read()

        tags = [b'Author', b'Creator', b'Producer', b'Title']
        
        for tag in tags:
            # Match /Tag (value) handling escaped characters inside
            # In PDF, strings in parentheses can contain escaped parens \( or \).
            pattern_str = rb'/' + tag + rb'\s*\((?:[^()\\]|\\.)*\)'
            data = re.sub(pattern_str, rb'/' + tag + rb' ()', data)
            
            # PDF hex string format: /Tag <hex_value>
            pattern_hex = rb'/' + tag + rb'\s*<[0-9a-fA-F]*>'
            data = re.sub(pattern_hex, rb'/' + tag + rb' <>', data)
            
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error using regex fallback: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Scrub metadata (Author, Creator, Producer, Title) from a PDF file.")
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("output_pdf", nargs="?", help="Path to the output PDF file (optional)")
    
    args = parser.parse_args()
    
    input_path = args.input_pdf
    if not os.path.isfile(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)
        
    output_path = args.output_pdf
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"

    print(f"Processing '{input_path}' -> '{output_path}'")

    pdf_lib, lib_name = try_import_pypdf()
    success = False
    
    if pdf_lib and lib_name in ["pypdf", "PyPDF2"]:
        print(f"Using {lib_name} for metadata scrubbing...")
        success = scrub_with_pypdf(pdf_lib, lib_name, input_path, output_path)
    
    if not success:
        print("Using regex fallback for metadata scrubbing...")
        success = scrub_with_regex(input_path, output_path)
        
    if success:
        print("Metadata successfully scrubbed!")
    else:
        print("Failed to scrub metadata.")
        sys.exit(1)

if __name__ == "__main__":
    main()
