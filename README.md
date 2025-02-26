# cs50x-finance

This project is a web-based application for managing a virtual stock trading portfolio. It allows users to register, log in, buy and sell stocks, view their portfolio, and track their transaction history.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/KamogeloMahlake/cs50x-finance.git
    cd cs50x-finance
    ```

2. Set up a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    export FLASK_APP=app.py
    flask run
    ```

## Usage

1. Run the Flask application:
    ```bash
    flask run
    ```

2. Open a web browser and navigate to `http://127.0.0.1:5000`.

3. Register a new account and log in.

4. Use the navigation bar to buy stocks, view your portfolio, sell stocks, and view your transaction history.

## Routes

- `/`: Show portfolio of stocks
- `/buy`: Buy shares of stock
- `/history`: Show history of transactions
- `/login`: Log user in
- `/logout`: Log user out
- `/quote`: Get stock quote
- `/register`: Register user
- `/sell`: Sell shares of stock
- `/add`: Add money to account

## Files

- `app.py`: The main Flask application file that defines the routes and logic for the web app.
- `helpers.py`: A helper module that provides utility functions for the application.