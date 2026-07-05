from datetime import datetime, timezone, timedelta

import requests

SINA_URL = "https://hq.sinajs.cn/list="
PREFIX = "nf_"  # 新浪财经股指期货前缀

HEADERS = {
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def is_trading_time() -> dict:
    """返回当前交易状态 {'open': bool, 'phase': str}"""
    now = datetime.now(timezone(timedelta(hours=8)))
    weekday = now.weekday()
    h, m = now.hour, now.minute

    if weekday >= 5:
        return {"open": False, "phase": "休市"}

    minute_of_day = h * 60 + m
    morning_start, morning_end = 9 * 60 + 30, 11 * 60 + 30
    afternoon_start, afternoon_end = 13 * 60, 15 * 60

    if morning_start <= minute_of_day <= morning_end:
        return {"open": True, "phase": "上午交易中"}
    if afternoon_start <= minute_of_day < afternoon_end:
        return {"open": True, "phase": "下午交易中"}
    if afternoon_end <= minute_of_day:
        return {"open": False, "phase": "已收盘"}
    return {"open": False, "phase": "盘前"}


def get_realtime_price(code: str) -> float | None:
    """查询单个合约的最新价，返回 float，失败返回 None"""
    try:
        resp = requests.get(
            f"{SINA_URL}{PREFIX}{code}",
            headers=HEADERS,
            timeout=10,
        )
        resp.encoding = "gbk"
        text = resp.text.strip()

        if not text or "=" not in text:
            return None

        # nf_ 格式：var hq_str_nf_IF2606="开盘,最高,最低,最新价,..."
        # 第4个字段（index=3）是最新价
        data_part = text.split('"')[1]
        fields = data_part.split(",")
        if len(fields) < 4:
            return None

        price_str = fields[3].strip()
        return float(price_str) if price_str else None

    except Exception:
        return None


def get_index_price(code: str) -> float | None:
    """查询指数行情，返回最新价。code 如 'sh000905'（中证500）、'sh000852'（中证1000）"""
    try:
        resp = requests.get(
            f"{SINA_URL}{code}",
            headers=HEADERS,
            timeout=10,
        )
        resp.encoding = "gbk"
        text = resp.text.strip()
        if not text or "=" not in text:
            return None
        # 格式：var hq_str_sh000905="...,最新价,..."
        data_part = text.split('"')[1]
        fields = data_part.split(",")
        price_str = fields[3].strip() if len(fields) >= 4 else ""
        return float(price_str) if price_str else None
    except Exception:
        return None


def batch_get_prices(codes: list[str]) -> dict[str, float | None]:
    """批量查询多个合约，一次 HTTP 请求，返回 {code: price_or_None}"""
    if not codes:
        return {}

    query = ",".join(f"{PREFIX}{c}" for c in codes)
    try:
        resp = requests.get(
            f"{SINA_URL}{query}",
            headers=HEADERS,
            timeout=10,
        )
        resp.encoding = "gbk"
        text = resp.text.strip()
    except Exception:
        return {c: None for c in codes}

    result = {}
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for i, code in enumerate(codes):
        if i < len(lines):
            line = lines[i]
            if "=" in line and '"' in line:
                data_part = line.split('"')[1]
                fields = data_part.split(",")
                if len(fields) >= 4:
                    price_str = fields[3].strip()
                    try:
                        result[code] = float(price_str) if price_str else None
                    except ValueError:
                        result[code] = None
                else:
                    result[code] = None
            else:
                result[code] = None
        else:
            result[code] = None
    return result
