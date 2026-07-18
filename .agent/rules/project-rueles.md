---
trigger: always_on
glob:
description: Project rules for PDF editor
---
This project contains a Chrome extension and a backend server for PDF editing.

The Chrome extension is located in the "extension" directory.
The backend server is located in the "backend" directory.
Backend server is a Python application that uses venv and FastAPI.

When extension is loaded in Chrome, users can upload a PDF file and it is sent to the backend server.
Backend server processes the PDF file and returns HTML code of the PDF file.
This HTML code is then displayed in the Chrome extension and it is editable.
