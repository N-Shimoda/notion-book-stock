# Notion Book Stock
## About
**Notion Book Stock** is a laptop application for scanning barcodes of books and adding them into Notion database.

### Notes
- Entire codes are implemented with Python.
- Internet connection is required.

## Usage
### 1. Setup Python environment
Package dependencies are written in `environment.yml`.
```bash
conda env create -n app-books -f environment.yml
```

### 2. Launch application
App can be launched by executing `gui.py`.
```bash
python gui.py
```

## Files & Directories
- `gui.py`: toplevel
- `src`: backend codes
    + `github.py`
    + `google_books.py`
    + `notion.py`
- `icons`
- `environment.yml`: Package information for conda.
- `bookdata.json`: List of current books in the database.
- `experiments`: Programs used during the development.