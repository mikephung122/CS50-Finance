import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    purchases = db.execute("SELECT symbol, sum(shares) AS total_shares, price FROM transactions WHERE user_id = :user_id AND action='purchase' GROUP BY symbol, price",
                          user_id=session["user_id"])
    sales = db.execute("SELECT symbol, sum(shares) as total_shares, price FROM transactions WHERE user_id = :user_id AND action='sale' GROUP BY symbol, price",
                          user_id=session["user_id"])

    stocks = {}
    stock_value = 0

    for purchase in purchases:
        stocks[purchase['symbol']] = purchase

    for sale in sales:
        stocks[sale['symbol']]['total_shares'] = stocks[sale['symbol']]['total_shares'] - sale['total_shares']

    stocks = list(stocks.values())

    for stock in stocks:
        stock_value = stock_value + (stock['price'] * stock['total_shares'])

    users = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])

    total_networth = users[0]['cash'] + stock_value
    print(stocks)
    return render_template("index.html", stocks=stocks, user=users[0], total_networth=total_networth)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    if request.method == "POST":
        lookup_response = lookup(request.form.get("symbol").upper())
        if lookup_response is None:
            return apology("Could not find symbol.")

        rows = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])
        total_cost = lookup_response['price'] * int(request.form.get('shares'))
        user_cash = rows[0]['cash']
        if user_cash < total_cost:
            return apology("Insufficient cash.")

        else:
            db.execute("INSERT INTO transactions (user_id, action, symbol, shares, price) VALUES (:user_id, 'purchase', :symbol, :shares, :price)",
                          user_id=session["user_id"], symbol=request.form.get("symbol").upper(), shares=request.form.get('shares'), price=lookup_response['price'])
            db.execute("UPDATE users SET cash=:new_cash WHERE id=:user_id",
                          new_cash=(user_cash-total_cost), user_id=session["user_id"])
            return redirect("/")

@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("cash.html")

    if request.method == "POST":
        request.form.get("symbol")
        db.execute("INSERT INTO deposits (user_id, credit_card_type, credit_card_number, amount) VALUES (:user_id, :credit_card_type, :credit_card_number, :amount)",
                          user_id=session["user_id"], credit_card_type=request.form.get("credit_card_type"), credit_card_number=request.form.get('credit_card_number'), amount=request.form.get('amount'))
        rows = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])
        user_cash = rows[0]['cash']
        db.execute("UPDATE users SET cash=:new_cash WHERE id=:user_id",
                          new_cash=(user_cash+float(request.form.get('amount'))), user_id=session["user_id"])
        return redirect("/")

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get('username')
    database_usernames = db.execute("SELECT username FROM users")
    current_usernames = []
    for row in database_usernames:
        current_usernames.append(row['username'])
    print("Input username is {}".format(username))
    print("Current usernames are: {}".format(current_usernames))
    print(isinstance(username, str))
    print(username not in current_usernames)
    print((isinstance(username, str)) & (username not in current_usernames))
    print(jsonify(False))
    if ((isinstance(username, str)) & (username not in current_usernames)):
        return jsonify(False)
    else:
        return jsonify(True)



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM transactions WHERE user_id=:user_id", user_id=session["user_id"])
    print(history)
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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    if request.method == "GET":
        return render_template("quote.html")

    if request.method == "POST":
        lookup_response = lookup(request.form.get("symbol"))
        if lookup_response is None:
            return apology("Could not find symbol.")

        else:
            print(lookup_response)
            return render_template("quoted.html", lookup_response=lookup_response)

@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Check if a user with that username already exists
        if len(rows) != 0:
            return apology("username already exists.", 403)

        # Ensure password was submitted and matches the confirmation
        if not request.form.get("password"):
            return apology("must provide password", 403)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("confirmation must match password", 403)


        regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

        if (regex.search(request.form.get("password")) == None):
            return apology("password must contain at least one special character.", 403)

        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashed_password)", username=request.form.get("username"), hashed_password=generate_password_hash(request.form.get("password")))
            return render_template("login.html")




@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        return render_template("sell.html")

    if request.method == "POST":
        lookup_response = lookup(request.form.get("symbol").upper())
        if lookup_response is None:
            return apology("Could not find symbol.")

        purchases = db.execute("SELECT sum(shares) as total_shares FROM transactions WHERE user_id = :user_id AND symbol=:symbol and action='purchase'",
                          user_id=session["user_id"], symbol=request.form.get("symbol").upper())
        sales = db.execute("SELECT sum(shares) as total_shares FROM transactions WHERE user_id = :user_id AND symbol=:symbol and action='sale'",
                          user_id=session["user_id"], symbol=request.form.get("symbol").upper())

        if purchases[0]['total_shares'] is None:
            purchases[0]['total_shares'] = 0

        if sales[0]['total_shares'] is None:
            sales[0]['total_shares'] = 0

        user_shares = int(purchases[0]['total_shares']) - int(sales[0]['total_shares'])

        total_cost = lookup_response['price'] * int(request.form.get('shares'))
        users = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])
        user_cash = users[0]['cash']

        if int(request.form.get("shares")) > user_shares:
            return apology("Insufficient shares.")

        else:
            db.execute("INSERT INTO transactions (user_id, action, symbol, shares, price) VALUES (:user_id, 'sale', :symbol, :shares, :price)",
                          user_id=session["user_id"], symbol=request.form.get("symbol").upper(), shares=request.form.get('shares'), price=lookup_response['price'])
            db.execute("UPDATE users SET cash=:new_cash WHERE id=:user_id",
                          new_cash=(user_cash+total_cost), user_id=session["user_id"])
            return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
