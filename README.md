# files2pdf_bot

Converts uploaded files to PDF.

## Requirements

Python v3 (3.12.7)

```
pip install python-dotenv
pip install telegram
pip install python-telegram-bot reportlab pillow
pip install python-telegram-bot==13.13
pip install urllib3==1.26.15
```

## Usage

`/start` Says hello to user
`/convert` Convert uploaded files to a single PDF. 
`/clear` Clear all uploaded files from the user session.

### Supported formats

- .txt
- .doc
- .docx
- .odt
- .md
- .jpg
- .jpeg
- .webp
- .png
