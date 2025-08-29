# 🚀 SignalVerse

SignalVerse is a **professional, multi-scanner SaaS platform** providing real-time, high-quality crypto trading signals.  
It is built with **Python (backend scanners)**, **Supabase (database + realtime)**, and **Next.js (frontend dashboard + admin panel)**.

---

## 📌 Features

### 🔎 Scanners
- **Fawda Scanner** (WebSocket-based, multi-timeframe)
- **Nakel + Hadena logic** for advanced signal detection
- **Manual Scan** to backfill signals across all timeframes
- **Realtime updates** via Supabase

### 📊 Dashboard
- Built with **Next.js + Supabase**
- **Material UI (MUI)** for professional design
- Filters:
  - Symbol (multi-select dropdown)
  - Timeframe (checkbox select)
  - Status (active, confirmed, invalidated)
  - Signal Codes (multi-select)
- **Realtime DataGrid** with pagination, sorting, and search
- **Dark/Light mode toggle**
- **Export to CSV/Excel**

### 🛠 Admin Panel
- Manage users and subscriptions
- Manage scanners (activate/deactivate, schedules)
- View scanner health and logs

---

## 🗄 Database Schema (Supabase)

### `signals`
- `scannerType` (String, Indexed)
- `symbol` (String, Indexed)
- `timeframe` (String, Indexed)
- `signalCodes` (Array, Indexed)
- `signalId` (Unique, Indexed)
- `candleTimestamp` (Datetime)
- `entryPrice` (Float)
- `status` (String, Indexed)
- `metadata` (JSON)

### `scanner_configs`
- `scannerId` (Unique)
- `name`
- `description`
- `isActive` (Boolean)
- `cronSchedule`
- `config` (JSON)
- `lastRunTimestamp`
- `lastRunStatus`
- `lastErrorMessage`

### `user_profiles`
- `userId` (Unique, links to Supabase Auth)
- `subscriptionTier` (free, pro, enterprise)
- `stripeCustomerId`
- `preferences` (JSON)

---

## ⚙️ Installation

### 1. Clone the repo
```bash
git clone https://github.com/drjimmy1990/Signal-verse.git
cd Signal-verse
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```
- Configure `.env` with your Supabase keys:
  ```env
  SUPABASE_URL=https://<your-project>.supabase.co
  SUPABASE_KEY=<your-service-role-key>
  ```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Configure `.env.local` with your Supabase anon key:
  ```env
  NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
  ```

---

## ▶️ Usage

### Run Scanner
```bash
cd backend
python scanners/fawda_scanner.py
```

### Run Frontend
```bash
cd frontend
npm run dev
```
Visit: [http://localhost:3000](http://localhost:3000)

---

## 📈 Roadmap
- [ ] Add more scanners (Momentum, Volume, etc.)
- [ ] Stripe integration for subscriptions
- [ ] Custom dashboards with multi-scanner queries
- [ ] Alerts system (email, Telegram, Discord)
- [ ] API access for Pro users

---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## 📜 License
MIT License © 2025 SignalVerse
