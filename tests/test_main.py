import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import main

def test_try_import_pypdf_has_pypdf():
    # pypdf is installed in this environment
    lib, name = main.try_import_pypdf()
    assert name == "pypdf"
    assert lib is not None

@patch.dict('sys.modules', {'pypdf': None})
def test_try_import_pypdf_has_pypdf2_no_pypdf():
    # Hide pypdf, leaving PyPDF2
    lib, name = main.try_import_pypdf()
    assert name == "PyPDF2"
    assert lib is not None

@patch.dict('sys.modules', {'pypdf': None, 'PyPDF2': None})
def test_try_import_pypdf_has_pdfplumber_only():
    lib, name = main.try_import_pypdf()
    assert name == "pdfplumber"
    assert lib is not None

@patch.dict('sys.modules', {'pypdf': None, 'PyPDF2': None, 'pdfplumber': None})
def test_try_import_pypdf_has_none():
    lib, name = main.try_import_pypdf()
    assert name is None
    assert lib is None

def test_scrub_with_pypdf_pdfplumber_fallback(capsys):
    result = main.scrub_with_pypdf(None, "pdfplumber", "in.pdf", "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "pdfplumber found but writing requires pypdf/PyPDF2. Falling back to regex" in captured.out

def test_scrub_with_pypdf_success():
    mock_pdf_lib = MagicMock()
    mock_reader = MagicMock()
    mock_writer = MagicMock()
    
    mock_pdf_lib.PdfReader.return_value = mock_reader
    mock_pdf_lib.PdfWriter.return_value = mock_writer
    
    mock_reader.pages = ["page1", "page2"]
    
    with patch("builtins.open", MagicMock()) as mock_open:
        result = main.scrub_with_pypdf(mock_pdf_lib, "pypdf", "in.pdf", "out.pdf")
        
    assert result is True
    mock_pdf_lib.PdfReader.assert_called_once_with("in.pdf")
    mock_pdf_lib.PdfWriter.assert_called_once()
    mock_writer.append_pages_from_reader.assert_called_once_with(mock_reader)
    mock_writer.add_metadata.assert_called_once_with({
        "/Author": "",
        "/Creator": "",
        "/Producer": "",
        "/Title": ""
    })
    mock_open.assert_called_once_with("out.pdf", "wb")
    mock_writer.write.assert_called_once()

def test_scrub_with_pypdf_exception(capsys):
    mock_pdf_lib = MagicMock()
    mock_pdf_lib.PdfReader.side_effect = Exception("File read error")
    
    result = main.scrub_with_pypdf(mock_pdf_lib, "pypdf", "in.pdf", "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Error using pypdf: File read error" in captured.out

def test_scrub_with_pypdf_file_not_found(capsys):
    mock_pdf_lib = MagicMock()
    mock_pdf_lib.PdfReader.side_effect = FileNotFoundError()
    
    result = main.scrub_with_pypdf(mock_pdf_lib, "pypdf", "in.pdf", "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Error using pypdf: File not found" in captured.out

def test_scrub_with_pypdf_permission_error(capsys):
    mock_pdf_lib = MagicMock()
    mock_pdf_lib.PdfReader.side_effect = PermissionError()
    
    result = main.scrub_with_pypdf(mock_pdf_lib, "pypdf", "in.pdf", "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Error using pypdf: Permission denied" in captured.out

def test_scrub_with_pypdf_os_error(capsys):
    mock_pdf_lib = MagicMock()
    mock_pdf_lib.PdfReader.side_effect = OSError("OS Error")
    
    result = main.scrub_with_pypdf(mock_pdf_lib, "pypdf", "in.pdf", "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Error using pypdf: OS error occurred" in captured.out

def test_validate_paths_invalid_type():
    with pytest.raises(TypeError):
        main.validate_paths(123, "out.pdf")

def test_validate_paths_empty_string():
    with pytest.raises(ValueError):
        main.validate_paths("  ", "out.pdf")

def test_validate_paths_identical():
    with pytest.raises(ValueError):
        main.validate_paths("in.pdf", "in.pdf")

def test_scrub_with_pypdf_validation_error(capsys):
    result = main.scrub_with_pypdf(MagicMock(), "pypdf", 123, "out.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Validation Error:" in captured.out

def test_scrub_with_regex_validation_error(capsys):
    result = main.scrub_with_regex("in.pdf", "in.pdf")
    assert result is False
    captured = capsys.readouterr()
    assert "Validation Error:" in captured.out

def test_scrub_with_regex_success():
    input_data = b"""
    %PDF-1.4
    /Author (Secret Author \\(hidden\\))
    /Creator <414243>
    /Producer (Some Producer)
    /Title <444546>
    """
    
    mock_open = MagicMock()
    # first open reads input_data, second open writes to output
    mock_file = MagicMock()
    mock_file.read.return_value = input_data
    
    # We need an open that works as a context manager and returns different things based on the mode.
    # We can handle it with side_effect
    
    write_mock = MagicMock()
    
    def open_side_effect(path, mode):
        m = MagicMock()
        if mode == "rb":
            m.__enter__.return_value.read.return_value = input_data
        elif mode == "wb":
            m.__enter__.return_value.write = write_mock
        return m

    with patch("builtins.open", side_effect=open_side_effect) as mocked_open:
        result = main.scrub_with_regex("in.pdf", "out.pdf")
        
    assert result is True
    assert mocked_open.call_count == 2
    
    # Check the written data
    write_mock.assert_called_once()
    written_data = write_mock.call_args[0][0]
    
    assert b"/Author ()" in written_data
    assert b"/Creator <>" in written_data
    assert b"/Producer ()" in written_data
    assert b"/Title <>" in written_data
    
    assert b"Secret Author" not in written_data
    assert b"414243" not in written_data

def test_scrub_with_regex_exception(capsys):
    with patch("builtins.open", side_effect=Exception("Unknown Error")):
        result = main.scrub_with_regex("in.pdf", "out.pdf")
        
    assert result is False
    captured = capsys.readouterr()
    assert "Error using regex fallback: Unknown Error" in captured.out

def test_scrub_with_regex_file_not_found(capsys):
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = main.scrub_with_regex("in.pdf", "out.pdf")
        
    assert result is False
    captured = capsys.readouterr()
    assert "Error using regex fallback: File not found" in captured.out

def test_scrub_with_regex_permission_error(capsys):
    with patch("builtins.open", side_effect=PermissionError()):
        result = main.scrub_with_regex("in.pdf", "out.pdf")
        
    assert result is False
    captured = capsys.readouterr()
    assert "Error using regex fallback: Permission denied" in captured.out

def test_scrub_with_regex_os_error(capsys):
    with patch("builtins.open", side_effect=OSError("OS Error")):
        result = main.scrub_with_regex("in.pdf", "out.pdf")
        
    assert result is False
    captured = capsys.readouterr()
    assert "Error using regex fallback: OS error occurred" in captured.out

@patch("sys.argv", ["main.py", "invalid.pdf"])
def test_main_invalid_input(capsys):
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input file 'invalid.pdf' does not exist." in captured.out

@patch("sys.argv", ["main.py", "valid.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=False)
def test_main_unreadable_input(mock_access, mock_isfile, capsys):
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input file 'valid.pdf' is not readable." in captured.out

@patch("sys.argv", ["main.py", "valid.pdf", "valid.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=True)
def test_main_identical_paths(mock_access, mock_isfile, capsys):
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input and output paths cannot be identical to prevent data loss." in captured.out

@patch("sys.argv", ["main.py", "valid.pdf", "out.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=True)
@patch("os.path.isdir", return_value=False)
@patch("os.path.dirname", return_value="some_dir")
def test_main_output_dir_missing(mock_dirname, mock_isdir, mock_access, mock_isfile, capsys):
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Output directory 'some_dir' does not exist." in captured.out

@patch("sys.argv", ["main.py", "valid.pdf", "out.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=True)
@patch("os.path.isdir", return_value=True)
@patch("main.try_import_pypdf")
@patch("main.scrub_with_pypdf")
def test_main_pypdf_success(mock_scrub_pypdf, mock_try_import, mock_isdir, mock_access, mock_isfile, capsys):
    mock_try_import.return_value = (MagicMock(), "pypdf")
    mock_scrub_pypdf.return_value = True
    
    main.main()
    
    captured = capsys.readouterr()
    assert "Processing 'valid.pdf' -> 'out.pdf'" in captured.out
    assert "Using pypdf for metadata scrubbing..." in captured.out
    assert "Metadata successfully scrubbed!" in captured.out
    mock_scrub_pypdf.assert_called_once()

@patch("sys.argv", ["main.py", "valid.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=True)
@patch("os.path.isdir", return_value=True)
@patch("main.try_import_pypdf")
@patch("main.scrub_with_regex")
def test_main_regex_fallback_success(mock_scrub_regex, mock_try_import, mock_isdir, mock_access, mock_isfile, capsys):
    # Simulate pdfplumber or none to trigger fallback
    mock_try_import.return_value = (MagicMock(), "pdfplumber")
    mock_scrub_regex.return_value = True
    
    main.main()
    
    captured = capsys.readouterr()
    # verify default output generation
    assert "Processing 'valid.pdf' -> 'valid_clean.pdf'" in captured.out
    assert "Using regex fallback for metadata scrubbing..." in captured.out
    assert "Metadata successfully scrubbed!" in captured.out
    mock_scrub_regex.assert_called_once_with("valid.pdf", "valid_clean.pdf")

@patch("sys.argv", ["main.py", "valid.pdf"])
@patch("os.path.isfile", return_value=True)
@patch("os.access", return_value=True)
@patch("os.path.isdir", return_value=True)
@patch("main.try_import_pypdf")
@patch("main.scrub_with_pypdf")
@patch("main.scrub_with_regex")
def test_main_both_fail(mock_scrub_regex, mock_scrub_pypdf, mock_try_import, mock_isdir, mock_access, mock_isfile, capsys):
    mock_try_import.return_value = (MagicMock(), "pypdf")
    mock_scrub_pypdf.return_value = False
    mock_scrub_regex.return_value = False
    
    with pytest.raises(SystemExit) as e:
        main.main()
        
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Using pypdf for metadata scrubbing..." in captured.out
    assert "Using regex fallback for metadata scrubbing..." in captured.out
    assert "Failed to scrub metadata." in captured.out
    mock_scrub_pypdf.assert_called_once()
    mock_scrub_regex.assert_called_once()
