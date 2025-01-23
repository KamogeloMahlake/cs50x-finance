import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    portfolio = db.execute(
        "SELECT symbol, shares FROM portfolio WHERE user_id = ?", session["user_id"])
    cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    total = cash[0]["cash"]
    if portfolio:
        for i in portfolio:
            i["price"] = lookup(i["symbol"])["price"]
            i["total_share_price"] = round(i["price"] * i["shares"], 2)
            total += i["total_share_price"]
            i["price"] = usd(i["price"])
            i["total_share_price"] = usd(i["total_share_price"])
    return render_template("index.html", cash=usd(cash[0]["cash"]), total=usd(total), portfolio=portfolio)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        data = lookup(symbol)
        if not symbol or not data:
            return apology("missing/invalid symbol")
        shares = request.form.get("shares")
        try:
            if not shares or int(shares) < 0 or "." in shares:
                return apology("missing shares")
        except ValueError:
            return apology("enter a number")
        current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        total_value = int(shares) * float(data["price"])

        new_cash = current_cash[0]["cash"] - total_value

        if new_cash < 0:
            return apology("not enough cash")
        current_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        db.execute("INSERT INTO history(cost, shares, symbol, type, date, user_id) VALUES(?, ?, ?, ?, ?, ?)", float(
            data["price"]), int(shares), data["symbol"], "buy", current_date, session["user_id"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])
        portfolio = db.execute(
            "SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], data["symbol"])

        if portfolio:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                       (int(shares) + portfolio[0]["shares"]), session["user_id"], data["symbol"])
        else:
            db.execute("INSERT INTO portfolio(symbol, shares, price, user_id) VALUES(?, ?, ?, ?)",
                       data["symbol"], int(shares), float(data["price"]), session["user_id"])
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute(
        "SELECT symbol, shares, cost, date FROM history WHERE user_id = ?", session["user_id"])
    for i in history:
        i["cost"] = usd(i["cost"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("missing symbol")
        data = lookup(symbol)
        if not data:
            return apology("invalid symbol")
        data["price"] = usd(data["price"])
        return render_template("quoted.html", data=data)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation or confirmation != password:
            return apology("password must be the same", 400)

        try:
            session["user_id"] = db.execute(
                "INSERT INTO users(username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        except ValueError:
            return apology("user already exists, try login", 400)

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    symbols = db.execute(
        "SELECT symbol, shares FROM portfolio WHERE user_id = ?", session["user_id"])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        for i in symbols:
            if i["symbol"] == symbol:
                try:
                    if not shares or int(shares) < 0 or "." in shares or i["shares"] < int(shares):
                        return apology("missing shares")
                    else:
                        data = lookup(symbol)
                        current_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                        db.execute("INSERT INTO history(cost, shares, symbol, type, date, user_id) VALUES(?, ?, ?, ?, ?, ?)", float(
                            data["price"]), -int(shares), data["symbol"], "sell", current_date, session["user_id"])
                        money = int(shares) * float(data["price"])
                        cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
                        db.execute("UPDATE users SET cash = ? WHERE id = ?",
                                   (cash[0]["cash"] + money), session["user_id"])

                        current_shares = i["shares"] - int(shares)
                        if current_shares == 0:
                            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                                       session["user_id"], data["symbol"])
                        else:
                            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                                       current_shares, session["user_id"], data["symbol"])

                        return redirect("/")
                except ValueError:
                    return apology("Enter a number")
        else:
            return apology("Enter correct symbol")
    else:
        return render_template("sell.html", symbols=symbols)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_money():
    if request.method == "POST":
        money = request.form.get("money")

        try:
            if not money or int(money) < 1:
                return apology("enter correct value")
            else:
                cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
                db.execute("UPDATE users SET cash = ? WHERE id = ?",
                           (cash[0]["cash"] + int(money)), session["user_id"])
                return redirect("/")
        except ValueError:
            return apology("enter a number")
    else:
        return render_template("add.html")
