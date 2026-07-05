import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from futures_api import get_realtime_price, batch_get_prices

# 测试单个查询
codes = ["IF2606", "IH2606", "IC2606", "IM2606"]
print("=== 单合约查询 ===")
for code in codes:
    price = get_realtime_price(code)
    if price is not None:
        print(f"  [OK] {code} 最新价: {price:.2f}")
    else:
        print(f"  [FAIL] {code} 获取失败")

# 测试批量查询
print("\n=== 批量查询 ===")
prices = batch_get_prices(codes)
for code, price in prices.items():
    if price is not None:
        print(f"  [OK] {code} 最新价: {price:.2f}")
    else:
        print(f"  [FAIL] {code} 获取失败")

# 测试价格差值
print("\n=== 价格差值 ===")
if prices.get("IF2606") is not None and prices.get("IH2606") is not None:
    diff = prices["IF2606"] - prices["IH2606"]
    print(f"  IF2606 - IH2606 = {diff:+.2f}")
