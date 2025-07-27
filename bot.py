import ccxt
import time
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

exchange = ccxt.mexc()
MIN_PUMP_PERCENT = 5
MIN_VOLUME_USDT = 50000
CHECK_INTERVAL = 300  # 5 хвилин
sent_coins = set()

def get_top_usdt_symbols(limit=100):
    markets = exchange.load_markets()
    return [symbol for symbol in markets if symbol.endswith('/USDT')][:limit]

def fetch_candles(symbol):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe='5m', limit=3)
    except Exception:
        return []

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def check_pumps():
    symbols = get_top_usdt_symbols()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Перевірка {len(symbols)} монет...")

    for symbol in symbols:
        candles = fetch_candles(symbol)
        if len(candles) < 3:
            continue

        previous = candles[-3][4]  # close 10 хв тому
        current = candles[-1][4]   # останній close

        if previous == 0:
            continue

        percent_change = ((current - previous) / previous) * 100
        volume = candles[-1][5]

        market_symbol = f"{symbol.split('/')[0]}_{symbol.split('/')[1]}"
        link = f"https://www.mexc.com/ru-RU/exchange/{market_symbol}"

        if percent_change >= MIN_PUMP_PERCENT and volume >= MIN_VOLUME_USDT and market_symbol not in sent_coins:
            message = (
                f"🚨 *Новий памп!*\n"
                f"🔹 Coin: ${market_symbol}\n"
                f"📈 Зріст: {percent_change:.2f}% за 10 хв\n"
                f"💵 Обʼєм: ${int(volume):,}\n"
                f"🔗 [Торгувати на MEXC]({link})\n"
                f"🕒 {datetime.now().strftime('%H:%M:%S')}"
            )
            send_telegram_message(message)
            sent_coins.add(market_symbol)

while True:
    check_pumps()
    time.sleep(CHECK_INTERVAL)