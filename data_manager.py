import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "contracts.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(contracts: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(contracts, f, ensure_ascii=False, indent=2)


def get_all() -> list[dict]:
    """返回所有合约列表"""
    return _load()


CONTRACT_MAP = {
    "IF": "沪深300股指期货",
    "IH": "上证50股指期货",
    "IC": "中证500股指期货",
    "IM": "中证1000股指期货",
}
EXCHANGE = "CFFEX"


def parse_code(code: str) -> dict | None:
    """解析合约代码，自动补全名称和交易所。如 'IF2606' → {name, exchange}"""
    code = code.strip().upper()
    if len(code) < 2:
        return None
    prefix = code[:2]
    name_prefix = CONTRACT_MAP.get(prefix)
    if not name_prefix:
        return None
    return {
        "name": f"{name_prefix}{code[2:]}",
        "exchange": EXCHANGE,
    }


def add_contract(code: str) -> bool:
    """添加合约（自动解析名称/交易所），成功返回 True，已存在返回 False"""
    info = parse_code(code)
    if info is None:
        return False
    contracts = _load()
    if any(c["code"] == code for c in contracts):
        return False
    contracts.append({"code": code, "name": info["name"], "exchange": info["exchange"]})
    _save(contracts)
    return True


def delete_contract(code: str) -> bool:
    """删除合约，成功返回 True，不存在返回 False"""
    contracts = _load()
    new_list = [c for c in contracts if c["code"] != code]
    if len(new_list) == len(contracts):
        return False
    _save(new_list)
    return True


def get_by_code(code: str) -> dict | None:
    """按合约代码查找"""
    contracts = _load()
    for c in contracts:
        if c["code"] == code:
            return c
    return None
