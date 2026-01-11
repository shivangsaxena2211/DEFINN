from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
from functools import wraps
import os
import re
import requests



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



app = Flask(__name__)


app.secret_key = "definn_super_secret_key_123"


CORS(app, supports_credentials=True)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])



def get_user():
    """Returns logged in user's user_id from Flask session"""
    return session.get("user_id")


def login_required(f):
    """Protects HTML routes - redirects to login page if not logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Protects API routes - returns JSON error if not logged in"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated



@app.route("/")
def home():
   
    if get_user():
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/profile", methods=["GET"])
@api_login_required
def api_profile():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, email, user_id FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "name": row["name"],
        "email": row["email"],
        "user_id": row["user_id"]
    }), 200

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("Dashboard.html")


@app.route("/stocks")
@login_required
def stocks_page():
    return render_template("stock.html")


@app.route("/crypto")
@login_required
def crypto_page():
    return render_template("crypto.html")


@app.route("/payments")
@login_required
def payments_page():
    return render_template("payment.html")



@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE email=? AND password=?",
        (email.strip().lower(), password)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = row["user_id"]
    return jsonify({"message": "Login successful"}), 200


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password required"}), 400

    email = email.strip().lower()

    conn = get_db()
    cur = conn.cursor()

   
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered"}), 400

    user_id = f"USER{int(datetime.now().timestamp())}"

   
    cur.execute(
        "INSERT INTO users (user_id, name, email, password) VALUES (?, ?, ?, ?)",
        (user_id, name.strip(), email, password)
    )

    
    cur.execute(
        "INSERT INTO wallet (user_id, balance) VALUES (?, ?)",
        (user_id, 50000)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Registration successful"}), 201


@app.route("/api/me", methods=["GET"])
def api_me():
    """Front-end can call this to verify user session."""
    if not get_user():
        return jsonify({"logged_in": False}), 200
    return jsonify({"logged_in": True, "user_id": get_user()}), 200




@app.route("/api/wallet", methods=["GET"])
@api_login_required
def wallet():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Wallet not found"}), 404

    return jsonify({"balance": float(row["balance"])}), 200


@app.route("/api/send", methods=["POST"])
@api_login_required
def send_money():
    user_id = get_user()
    data = request.json or {}

    to_user = data.get("to")
    amount = data.get("amount")

    if not to_user or amount is None:
        return jsonify({"error": "Receiver and amount required"}), 400

    amount = float(amount)
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Wallet not found"}), 404

    balance = float(row["balance"])
    if balance < amount:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    
    cur.execute(
        "UPDATE wallet SET balance = balance - ? WHERE user_id=?",
        (amount, user_id)
    )

   
    cur.execute("""
        INSERT INTO transactions (from_user, to_user, amount, type, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, to_user, amount, "Sent", datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({"message": "Payment successful"}), 200


@app.route("/api/transactions", methods=["GET"])
@api_login_required
def transactions():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM transactions
        WHERE from_user=? OR to_user=?
        ORDER BY date DESC
    """, (user_id, user_id))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200



@app.route("/api/crypto/buy", methods=["POST"])
@api_login_required
def crypto_buy():
    user_id = get_user()
    data = request.json or {}

    symbol = data.get("symbol")
    quantity = data.get("quantity")
    price = data.get("price")

    if not symbol or quantity is None or price is None:
        return jsonify({"error": "symbol, quantity, price required"}), 400

    quantity = float(quantity)
    price = float(price)
    if quantity <= 0 or price <= 0:
        return jsonify({"error": "quantity and price must be > 0"}), 400

    cost = quantity * price

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Wallet not found"}), 404

    balance = float(row["balance"])
    if balance < cost:
        conn.close()
        return jsonify({"error": "Insufficient wallet balance"}), 400

   
    cur.execute(
        "UPDATE wallet SET balance = balance - ? WHERE user_id=?",
        (cost, user_id)
    )

    
    cur.execute("""
        INSERT INTO crypto_holdings (user_id, symbol, quantity, buy_price, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, symbol, quantity, price, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({"message": "Crypto purchased successfully"}), 200


@app.route("/api/crypto/holdings", methods=["GET"])
@api_login_required
def crypto_holdings():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, quantity, buy_price, timestamp
        FROM crypto_holdings
        WHERE user_id=?
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route("/api/crypto/sell", methods=["POST"])
@api_login_required
def crypto_sell():
    user_id = get_user()
    data = request.json or {}

    symbol = data.get("symbol")
    quantity = data.get("quantity")
    price = data.get("price")

    if not symbol or quantity is None or price is None:
        return jsonify({"error": "symbol, quantity, price required"}), 400

    quantity = float(quantity)
    price = float(price)

    if quantity <= 0 or price <= 0:
        return jsonify({"error": "quantity and price must be > 0"}), 400

    conn = get_db()
    cur = conn.cursor()

    
    cur.execute("""
        SELECT id, quantity FROM crypto_holdings
        WHERE user_id=? AND symbol=?
        ORDER BY timestamp ASC
    """, (user_id, symbol))

    rows = cur.fetchall()
    total_qty = sum(float(r["quantity"]) for r in rows)

    if total_qty < quantity:
        conn.close()
        return jsonify({"error": "Insufficient crypto quantity"}), 400

    remaining = quantity

    for row in rows:
        row_id = row["id"]
        row_qty = float(row["quantity"])

        if remaining <= 0:
            break

        if row_qty <= remaining:
            cur.execute("DELETE FROM crypto_holdings WHERE id=?", (row_id,))
            remaining -= row_qty
        else:
            cur.execute(
                "UPDATE crypto_holdings SET quantity = quantity - ? WHERE id=?",
                (remaining, row_id)
            )
            remaining = 0

    
    credit = quantity * price
    cur.execute(
        "UPDATE wallet SET balance = balance + ? WHERE user_id=?",
        (credit, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Crypto sold successfully"}), 200


@app.route("/api/stocks/buy", methods=["POST"])
@api_login_required
def buy_stock():
    user_id = get_user()
    data = request.json or {}

    symbol = data.get("symbol")
    quantity = data.get("quantity")
    price = data.get("price")

    if not symbol or quantity is None or price is None:
        return jsonify({"error": "symbol, quantity, price required"}), 400

    quantity = int(quantity)
    price = float(price)

    if quantity <= 0 or price <= 0:
        return jsonify({"error": "quantity and price must be > 0"}), 400

    cost = quantity * price

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Wallet not found"}), 404

    balance = float(row["balance"])
    if balance < cost:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    
    cur.execute(
        "UPDATE wallet SET balance = balance - ? WHERE user_id=?",
        (cost, user_id)
    )

   
    cur.execute("""
        INSERT INTO stock_holdings (user_id, symbol, quantity, buy_price, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, symbol, quantity, price, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({"message": "Stock purchased"}), 200


@app.route("/api/stocks/sell", methods=["POST"])
@api_login_required
def sell_stock():
    user_id = get_user()
    data = request.json or {}

    symbol = data.get("symbol")
    quantity = data.get("quantity")
    price = data.get("price")

    if not symbol or quantity is None or price is None:
        return jsonify({"error": "symbol, quantity, price required"}), 400

    quantity = int(quantity)
    price = float(price)

    if quantity <= 0 or price <= 0:
        return jsonify({"error": "quantity and price must be > 0"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, quantity FROM stock_holdings
        WHERE user_id=? AND symbol=?
        ORDER BY timestamp ASC
    """, (user_id, symbol))

    rows = cur.fetchall()
    owned = sum(int(r["quantity"]) for r in rows)

    if owned < quantity:
        conn.close()
        return jsonify({"error": "Not enough stock"}), 400

    remaining = quantity
    for r in rows:
        row_id = r["id"]
        qty = int(r["quantity"])

        if remaining <= 0:
            break

        if qty <= remaining:
            cur.execute("DELETE FROM stock_holdings WHERE id=?", (row_id,))
            remaining -= qty
        else:
            cur.execute(
                "UPDATE stock_holdings SET quantity = quantity - ? WHERE id=?",
                (remaining, row_id)
            )
            remaining = 0

    credit = quantity * price
    cur.execute(
        "UPDATE wallet SET balance = balance + ? WHERE user_id=?",
        (credit, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Stock sold"}), 200


@app.route("/api/stocks/holdings", methods=["GET"])
@api_login_required
def stock_holdings():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, quantity, buy_price, timestamp
        FROM stock_holdings
        WHERE user_id=?
        ORDER BY timestamp DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route("/api/stocks/portfolio", methods=["GET"])
@api_login_required
def stock_portfolio():
    user_id = get_user()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, SUM(quantity) AS quantity
        FROM stock_holdings
        WHERE user_id=?
        GROUP BY symbol
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200

# ---------------------------
# AI Chatbot Helpers
# ---------------------------

def _safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def fetch_crypto_price(symbol: str):
    """
    Uses CoinGecko simple price endpoint.
    symbol examples: BTC, ETH
    """
    symbol = (symbol or "").strip().upper()

    mapping = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "ADA": "cardano"
    }

    coin_id = mapping.get(symbol)
    if not coin_id:
        return None

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "inr", "include_24hr_change": "true"}
    r = requests.get(url, params=params, timeout=8)
    data = r.json()

    price = data.get(coin_id, {}).get("inr")
    change_24h = data.get(coin_id, {}).get("inr_24h_change", 0)

    if price is None:
        return None

    return {
        "symbol": symbol,
        "price": float(price),
        "change_24h": float(change_24h)
    }

def compute_signal(change_24h: float):
    """
    Simple signal based on 24h change:
      - if down strongly => BUY (dip)
      - if up strongly => SELL / Take profit
      - else HOLD
    """
    if change_24h <= -3:
        return "BUY", 72
    elif change_24h >= 4:
        return "SELL", 70
    else:
        return "HOLD", 62

def parse_asset(message: str):
    """
    Extracts symbol from user message like:
    - BTC, ETH, RELIANCE, TCS
    """
    msg = (message or "").upper()

    crypto_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA"]
    for s in crypto_symbols:
        if re.search(rf"\b{s}\b", msg):
            return ("crypto", s)

    
    stock_symbols = [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","HINDUNILVR","SBIN",
        "KOTAKBANK","LT","AXISBANK","MARUTI","BHARTIARTL","ITC","BAJFINANCE","ASIANPAINT"
    ]
    for s in stock_symbols:
        if re.search(rf"\b{s}\b", msg):
            return ("stock", s)

    return (None, None)

@app.route("/api/chat", methods=["POST"])
@api_login_required
def api_chat():
    user_id = get_user()
    data = request.json or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Message required"}), 400
    
   
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    wallet_row = cur.fetchone()
    wallet_balance = float(wallet_row["balance"]) if wallet_row else 0.0

    
    cur.execute("""
        SELECT symbol, SUM(quantity) AS quantity
        FROM stock_holdings
        WHERE user_id=?
        GROUP BY symbol
    """, (user_id,))
    stock_holdings = [dict(r) for r in cur.fetchall()]

   
    cur.execute("""
        SELECT symbol, SUM(quantity) AS quantity
        FROM crypto_holdings
        WHERE user_id=?
        GROUP BY symbol
    """, (user_id,))
    crypto_holdings = [dict(r) for r in cur.fetchall()]

    conn.close()

    
    asset_type, symbol = parse_asset(message)

    
    if "SUMMARY" in message.upper() or "PORTFOLIO" in message.upper():
        stock_text = ", ".join([f"{h['symbol']} (Qty {h['quantity']})" for h in stock_holdings]) or "None"
        crypto_text = ", ".join([f"{h['symbol']} (Qty {h['quantity']})" for h in crypto_holdings]) or "None"

        reply = (
            f"Here’s your portfolio summary:\n\n"
            f"Universal Wallet Balance: ₹{wallet_balance:,.2f}\n\n"
            f"Stocks: {stock_text}\n"
            f"Crypto: {crypto_text}\n\n"
            f"Tip: Ask me like 'Should I buy BTC today?' or 'Should I sell RELIANCE?'."
        )
        return jsonify({"reply": reply, "signal": "INFO", "confidence": 90}), 200

   
    if asset_type == "crypto" and symbol:
        market = fetch_crypto_price(symbol)
        if not market:
            return jsonify(
                {"reply": f"I couldn’t fetch live data for {symbol}. Try BTC/ETH/BNB/SOL.", "signal": "INFO", "confidence": 55}
            ), 200

        signal, conf = compute_signal(market["change_24h"])
        price = market["price"]
        change = market["change_24h"]

        
        suggested_qty = 0
        if wallet_balance > 0:
            suggested_qty = round((wallet_balance * 0.05) / price, 6)  # 5% of wallet

        reply = (
            f"📌 Crypto Insight ({symbol})\n\n"
            f"Current Price: ₹{price:,.2f}\n"
            f"24h Change: {change:+.2f}%\n\n"
            f"Signal: {signal}  | Confidence: {conf}%\n\n"
            f"Reasoning:\n"
            f"- I used momentum from the last 24 hours.\n"
            f"- If market dips hard → BUY (good entry)\n"
            f"- If market pumps hard → SELL (profit booking)\n\n"
            f"Risk-managed suggestion:\n"
            f"- With ₹{wallet_balance:,.2f} wallet, consider max ~5% exposure.\n"
            f"- That is around ≈ {suggested_qty} {symbol} (demo estimate).\n\n"
            f"Disclaimer: This is educational and not financial advice."
        )

        return jsonify({"reply": reply, "signal": signal, "confidence": conf, "data": market}), 200

   
    if asset_type == "stock" and symbol:
        reply = (
            f"📌 Stock Insight ({symbol})\n\n"
            f"Signal: HOLD | Confidence: 64%\n\n"
            f"Reasoning:\n"
            f"- For demo, I use conservative rules without real NSE/BSE live feed.\n"
            f"- If you enable live stock API later, I can compute RSI + trend signals.\n\n"
            f"Portfolio Tip:\n"
            f"- Only buy if you have enough wallet balance and keep risk per trade low.\n\n"
            f"Try asking:\n"
            f"✅ 'Portfolio summary'\n"
            f"✅ 'Should I buy BTC today?'"
        )
        return jsonify({"reply": reply, "signal": "HOLD", "confidence": 64}), 200

    
    reply = (
        "I can analyze crypto + stocks for you.\n\n"
        "Try commands like:\n"
        "• Portfolio summary\n"
        "• Should I buy BTC today?\n"
        "• Should I sell ETH?\n"
        "• Should I buy RELIANCE?\n\n"
        "Note: Stocks are currently demo-analysis unless you connect a live market API."
    )
    return jsonify({"reply": reply, "signal": "INFO", "confidence": 80}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
