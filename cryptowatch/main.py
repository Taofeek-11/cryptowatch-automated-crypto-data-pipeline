import websocket
import json
import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import pandas as pd

news_url    = "https://www.coindesk.com/arc/outboundfeeds/rss/"
topcoin_url = "https://api.coingecko.com/api/v3/coins/markets"

news          = []
market        = []
crypto_prices = []

#============================== Storage ==============================
with sqlite3.connect("prices.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, coin TEXT, price REAL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, headline TEXT, author TEXT, published TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS market (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, symbol TEXT, price REAL, market_cap REAL, change_24h REAL)""")
print("✅ All tables created")

#============================== Functions ============================
def save_prices():
    rows = [(p['timestamp'], p['coin'], p['price']) for p in crypto_prices]
    with sqlite3.connect('prices.db') as conn:
        conn.cursor().executemany(
            "INSERT INTO prices (timestamp, coin, price) VALUES (?,?,?)", rows)
    print(f"✅ {len(rows)} price records saved")

def save_news():
    rows = [(n['timestamp'], n['Headline'], n['Author'], n['Published Date']) for n in news]
    with sqlite3.connect('prices.db') as conn:
        conn.cursor().executemany(
            "INSERT INTO news (timestamp, headline, author, published) VALUES (?,?,?,?)", rows)
    print(f"✅ {len(rows)} news records saved")

def save_market():
    rows = [(m['Coin Name'], m['Symbol'], m['Current Price'],
             m['Market Cap'], m['24h Change']) for m in market]
    with sqlite3.connect('prices.db') as conn:
        conn.cursor().executemany(
            "INSERT INTO market (name, symbol, price, market_cap, change_24h) VALUES (?,?,?,?,?)", rows)
    print(f"✅ {len(rows)} market records saved")

def on_open(ws):
    print('🔌 Connected to Binance live feed...')

def on_message(ws, message):
    data    = json.loads(message)
    stream  = data["stream"]
    payload = data["data"]
    price   = float(payload["p"])

    if "btcusdt"  in stream: coin = "BTC"
    elif "ethusdt"  in stream: coin = "ETH"
    elif "dogeusdt" in stream: coin = "DOGE"
    else: coin = stream.split("@")[0].upper()

    crypto_prices.append({
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'coin': coin,
        'price': price
    })
    print(f"[{crypto_prices[-1]['timestamp']}] {coin} = ${price:,.2f}  ({len(crypto_prices)}/20)")

    if len(crypto_prices) >= 20:
        print('✅ 20 readings collected!')
        ws.close()

def on_error(ws, error):
    print(f'❌ WebSocket Error: {error}')

def on_close(ws, code, msg):
    print('🔌 WebSocket connection closed')

#============================== Data Collection ======================
print('\n🚀 CryptoWatch Pipeline Starting...\n')

print('📰 Fetching news headlines...')
try:
    resp = requests.get(news_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup  = BeautifulSoup(resp.text, "xml")
    for item in soup.find_all('item')[:10]:
        news.append({
            'timestamp':      datetime.now().strftime('%H:%M:%S'),
            'Headline':       item.title.text,
            'Author':         item.creator.text,
            'Published Date': item.pubDate.text
        })
    print(f'✅ {len(news)} headlines fetched')
except requests.RequestException as e:
    print(f'❌ News Error: {e}')

print('\n📊 Fetching market overview...')
try:
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10}
    resp   = requests.get(topcoin_url, params=params, timeout=10)
    resp.raise_for_status()
    for coin in resp.json()[:10]:
        market.append({
            'Coin Name':     coin['name'],
            'Symbol':        coin['symbol'].upper(),
            'Current Price': coin['current_price'],
            'Market Cap':    coin['market_cap'],
            '24h Change':    coin['price_change_24h']
        })
    print(f'✅ {len(market)} coins fetched')
except requests.RequestException as e:
    print(f'❌ Market Error: {e}')

print('\n🔌 Connecting to live price feed...')
ws = websocket.WebSocketApp(
    "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/dogeusdt@trade",
    on_open=on_open, on_message=on_message,
    on_error=on_error, on_close=on_close
)
ws.run_forever()

#============================== Save to DB ===========================
save_prices()
save_news()
save_market()

#============================== Reports ==============================
print('\n📝 Generating reports...')

with open('report.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['timestamp', 'coin', 'price'])
    writer.writeheader()
    writer.writerows(crypto_prices)
print(f'✅ report.csv saved ({len(crypto_prices)} rows)')

with open('report.json', 'w') as f:
    report = {
        "generated_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price_summary": {},
        "top_coins":     market,
        "news_headlines": news
    }
    for coin in ['BTC', 'ETH', 'DOGE']:
        prices = [p['price'] for p in crypto_prices if p['coin'] == coin]
        if prices:
            report["price_summary"][coin] = {
                "highest": max(prices),
                "lowest":  min(prices),
                "average": round(sum(prices)/len(prices), 2)
            }
    json.dump(report, f, indent=4)
print('✅ report.json saved')

#============================== Summary ==============================
print('\n============================================')
print('📊 CRYPTOWATCH SESSION SUMMARY')
print('============================================')

prices_df = pd.DataFrame(crypto_prices)
coin_perf = prices_df.groupby('coin')['price'].agg(
    highest_price='max',
    lowest_price='min',
    avg_price='mean'
)
for symbol, row in coin_perf.iterrows():
    print(f"{symbol}  → High: ${row['highest_price']:,.2f}  Low: ${row['lowest_price']:,.2f}  Avg: ${row['avg_price']:,.2f}")

top_coin    = max(market, key=lambda x: x['Market Cap'])
top_gainer  = max(market, key=lambda x: x['24h Change'])
top_loser   = min(market, key=lambda x: x['24h Change'])

print(f"\nTop coin by market cap : {top_coin['Coin Name']}")
print(f"Biggest 24h gainer     : {top_gainer['Coin Name']} ({top_gainer['24h Change']:+.2f}%)")
print(f"Biggest 24h loser      : {top_loser['Coin Name']} ({top_loser['24h Change']:+.2f}%)")

sorted_news = sorted(news, key=lambda x: x['timestamp'])
print(f"\n📰 Latest headline:")
print(f"\t{sorted_news[0]['Headline']}")
print('============================================')
print('✅ Pipeline complete!')
