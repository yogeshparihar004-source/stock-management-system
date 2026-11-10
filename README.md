# Stock Management System (Python Flask)

A beginner-friendly mini project for managing product inventory and sales.

## Features
- Dashboard with product count, units in stock, and inventory value
- Add, edit, search, and delete products
- Unique SKU validation
- Low-stock alerts
- Record sales and automatically deduct stock
- Sales history
- SQLite database created automatically

## Requirements
- Python 3.10+
- pip

## Run on Windows
1. Extract this ZIP file.
2. Open Command Prompt in the project folder.
3. Create and activate a virtual environment (recommended):

   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bat
   pip install -r requirements.txt
   ```

5. Start the application:

   ```bat
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.

The SQLite file `stock.db` is created in the project directory the first time the app starts.

## Project structure

```text
stock_management_system/
├── app.py
├── requirements.txt
├── README.md
├── stock.db             # created on first run
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── products.html
    ├── product_form.html
    └── sales.html
```

## Notes
- This is an educational local demo, not a production-ready multi-user system.
- Before deployment, set a strong secret key, add authentication and CSRF protection, and use a production WSGI server instead of Flask's development server.
