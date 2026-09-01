# 🚀 CryptoWatch — Automated Crypto Data Pipeline

A fully automated data pipeline that collects, stores, 
and reports on live cryptocurrency data.

## 📦 Features
- 🔌 Live crypto prices via Binance WebSocket
- 📰 Crypto news headlines via CoinDesk RSS
- 📊 Top 10 coins by market cap via CoinGecko API
- 💾 SQLite storage for all data
- 📝 CSV and JSON report generation
- 📈 Automated session summary

## 🛠️ Tech Stack
- Python 3.x
- requests, BeautifulSoup4
- websocket-client
- SQLite3
- pandas
- schedule / APScheduler

## ⚙️ Installation

1. Clone the repository
```bash
git clone https://github.com/YourUsername/cryptowatch.git
cd cryptowatch
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the pipeline
```bash
python main.py
```

## 📊 Output
- `data/prices.db` — SQLite database with all readings
- `data/report.csv` — Price readings export
- `data/report.json` — Full session summary

## 📁 Project Structure

cryptowatch/
├── main.py # Main pipeline
├── requirements.txt # Dependencies
├── README.md # Documentation
└── data/ # Generated data (gitignored)


## ⚠️ Note
VPN may be required for Binance WebSocket access 
depending on your location.

## 👤 Author
Taofeek OLADIGBOLU — [GitHub Profile](https://github.com/Taofeek-11)
