#!/usr/bin/env python3
"""
BridgeScout — сравнение кросс-чейн маршрутов через Li.Fi API.
"""

import os
import sys
import requests
from decimal import Decimal

API_URL = os.getenv("LIFI_API_URL", "https://li.quest/v1/quote")
FROM_CHAIN = os.getenv("FROM_CHAIN")      # например "ethereum"
TO_CHAIN   = os.getenv("TO_CHAIN")        # например "polygon"
FROM_TOKEN = os.getenv("FROM_TOKEN")      # адрес токена или символ (в зависимости от API)
TO_TOKEN   = os.getenv("TO_TOKEN")        # адрес токена или символ
AMOUNT     = os.getenv("AMOUNT")          # в базовой единице (wei для ETH-подобных)

def fetch_routes():
    params = {
        "fromChain": FROM_CHAIN,
        "toChain": TO_CHAIN,
        "fromToken": FROM_TOKEN,
        "toToken": TO_TOKEN,
        "fromAmount": AMOUNT
    }
    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("routes", [])

def human_amount(amount_str, decimals):
    """Преобразует строку целого количества в Decimal с учётом decimals."""
    return Decimal(amount_str) / (Decimal(10) ** decimals)

def main():
    missing = [v for v in ("FROM_CHAIN","TO_CHAIN","FROM_TOKEN","TO_TOKEN","AMOUNT") if not os.getenv(v)]
    if missing:
        print(f"❗ Не заданы переменные окружения: {', '.join(missing)}")
        sys.exit(1)

    print(f"🔍 Запрос маршрутов: {FROM_TOKEN}@{FROM_CHAIN} → {TO_TOKEN}@{TO_CHAIN}, amount={AMOUNT}")
    try:
        routes = fetch_routes()
    except Exception as e:
        print("Ошибка запроса:", e)
        sys.exit(1)

    if not routes:
        print("Маршруты не найдены.")
        return

    # Сортируем по максимально получаемой сумме
    sorted_routes = sorted(
        routes,
        key=lambda r: Decimal(r["toAmount"]),
        reverse=True
    )

    print(f"\nНайдено {len(sorted_routes)} маршрутов. Топ‑5 по получаемой сумме:")
    for idx, route in enumerate(sorted_routes[:5], start=1):
        in_amt     = human_amount(route["fromAmount"], route["fromToken"]["decimals"])
        out_amt    = human_amount(route["toAmount"],   route["toToken"]["decimals"])
        protocols  = "→".join([step["tool"] for step in route.get("steps",[])])
        gas_cost   = Decimal(route.get("estimate",{}).get("gasCostUSD", "0"))
        print(f"{idx}. {protocols}")
        print(f"    send {in_amt} {route['fromToken']['symbol']} → get {out_amt} {route['toToken']['symbol']}")
        print(f"    estimated time: {route.get('estimate',{}).get('time', '?')}s, gas cost ≈ ${gas_cost:.2f}\n")

if __name__ == "__main__":
    main()
