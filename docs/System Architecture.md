# System Architecture (DEFINN FinTech Platform)

This document explains the overall system architecture of the **DEFINN FinTech Platform** using two levels of architecture diagrams:

- **Level 0 Architecture (Context Diagram)** – High-level interaction between the platform and external entities.
- **Level 1 Architecture (Module-Level DFD)** – Internal platform workflow showing authentication, dashboard hub, and module interactions.

---

## 1. Level 0 Architecture (Context Diagram)

### Overview
The **Level 0 system architecture** represents DEFINN FinTech Platform as a single unified system.  
It highlights the primary external stakeholders and APIs connected to the platform.

### Diagram (Level 0)

<img src="../images/level 0.jpeg" width="700">

### Entities & Interactions

#### 1. Customer
- Sends **Login Credentials** to the platform for authentication.
- Receives **Status / Reports** such as transaction confirmations, holdings, and wallet balances.

#### 2. Admin / Bank Headquarters
- Sends **Audit Requests** to the platform.
- Receives **Audit Logs / Reports** for compliance, monitoring, and internal verification.

#### 3. Regulatory APIs (RBI / NPCI)
- Platform shares **Compliance Data** with regulatory authorities.
- Ensures alignment with fintech regulations and transaction compliance.

#### 4. Binance API
- Platform fetches **live crypto market data** and trading information.
- Used for crypto module pricing, order execution logic, and chart updates.

#### 5. NSE Data Feed
- Platform fetches **market-related price feeds** used inside the stock module.
- Supports real-time updates required for trading calculations.

---

## 2. Level 1 Architecture (Module Level DFD)

### Overview
The **Level 1 system architecture** breaks down the internal functioning of the platform.

It shows how:
- Authentication is handled
- Dashboard acts as the central hub
- Wallet & holdings are managed
- Modules interact with APIs and storage

### Diagram (Level 1)


<img src="../images/level 1.jpeg" width="700">

---

## 3. Internal Functional Modules

### 3.1 Authentication Module (1.0 Authentication)
Purpose: To verify users before allowing access to financial modules.

- Takes user identity and credentials
- Performs validation and session initialization
- Grants access to dashboard hub after successful login

**Key Output:**
- Verified user session → passed to Dashboard Hub

---

### 3.2 Dashboard Hub (2.0 Dashboard Hub)
Purpose: The core controller module of the platform.

Dashboard hub:
- Acts as central UI control panel
- Routes requests to UPI, Stock, and Crypto modules
- Collects data from Wallet + Holdings to show in real-time

**Major Responsibilities:**
- User landing page after login
- Unified access to:
  - Wallet Balance
  - UPI Payments
  - Stock Holdings
  - Crypto Holdings
  - Real-time Price Feed

---

### 3.3 Wallet Data Stores (D1 Wallet, D2 Wallet)
Purpose: Store and update user balance and transaction-related wallet information.

- **D1 Wallet:** Main wallet storage (balance + primary wallet info)
- **D2 Wallet:** Additional wallet dataset (can be used for ledger, logs, secondary cache)

Used to:
- Validate whether user has enough funds
- Update wallet after transactions
- Show live wallet status on dashboard

---

### 3.4 UPI Payments Module (3.1 UPI Payments)
Purpose: Handle payments and transfers.

Flow:
1. User initiates UPI transaction
2. Dashboard routes to UPI module
3. UPI module updates wallet and returns success/failure status

Outputs:
- Updated wallet balance
- Payment logs (can be stored as transaction logs)

---

### 3.5 Stock Holdings Module
Purpose: Manage and store stock portfolio of user.

Functions:
- View holdings in dashboard
- Update portfolio after stock buy/sell
- Connect with NSE Data Feed for price updates (as shown in Level 0)

Data stored in:
- Stock Holdings store (portfolio database)

---

### 3.6 Crypto Holdings Module (3.2 Crypto Holdings)
Purpose: Manage crypto portfolio of user.

Flow:
1. Dashboard requests crypto data
2. Crypto module fetches live pricing from **Binance API**
3. Holdings are updated after buy/sell
4. Dashboard displays real-time holdings + prices

API:
- Binance API used for live price and trading reference

Data stored in:
- Crypto Holdings store

---

## 4. Data Flow Summary (End-to-End)

1. **Customer logs in**
2. Authentication validates and creates session
3. User enters **Dashboard Hub**
4. Dashboard fetches:
   - Wallet data (D1 / D2)
   - Stock holdings
   - Crypto holdings
5. Dashboard routes operations:
   - UPI payments → update wallet
   - Stock buy/sell → update stock holdings + wallet
   - Crypto buy/sell → update crypto holdings + wallet
6. External APIs provide real-time values:
   - Binance API → crypto prices/trades
   - NSE Data Feed → stock prices
7. Platform reports + logs support:
   - Admin audit requests
   - RBI/NPCI compliance exports

---

## 5. Architectural Benefits

### ✅ Modular Design
Each module is independent:
- Authentication
- Wallet
- UPI
- Stocks
- Crypto

This makes the system expandable and maintainable.

### ✅ Centralized Dashboard Hub
Single control unit for routing and UI management.

### ✅ Compliance Ready
Includes audit logging & regulatory integration at Level 0.

### ✅ Scalable API Integration
Supports external financial market APIs:
- Binance (crypto)
- NSE feed (stocks)

---

## Conclusion

