import streamlit as st
from streamlit_autorefresh import st_autorefresh

from futures_api import batch_get_prices, get_index_price, is_trading_time
from data_manager import get_all, add_contract, delete_contract

st.set_page_config(page_title="股指期货价格对比", layout="centered")
st.markdown("""
<style>
    .block-container { padding-top: 0.2rem !important; padding-bottom: 0 !important; }
    h1 { font-size: 1.2rem !important; margin-top: 0 !important; margin-bottom: 0.2rem !important; }
    h3 { font-size: 0.85rem !important; margin-top: 0.15rem !important; margin-bottom: 0.1rem !important; font-weight: 600 !important; }
    div[data-testid="stVerticalBlock"] > div { padding-top: 0 !important; padding-bottom: 0 !important; gap: 0.1rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    .stSelectbox, .stMetric { margin-bottom: 0 !important; }
    .stSelectbox > div > div { min-height: 28px !important; font-size: 0.8rem !important; }
    .stSelectbox label, .stMetric label { font-size: 0.75rem !important; }
    .stButton { margin-bottom: 0 !important; }
    .stButton button { font-size: 0.8rem !important; padding: 0.2rem 0.8rem !important; }
    .element-container { margin-bottom: 0 !important; }
    .row-widget.stButton { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)
trading_status = is_trading_time()
if trading_status["open"]:
    st_autorefresh(interval=15000, key="auto_refresh")
st.title("价格对比")

# ── 侧边栏：合约管理 ──
with st.sidebar:
    st.header("管理")

    with st.form("add_form", clear_on_submit=True):
        code = st.text_input("代码", placeholder="例如 IF2606").strip().upper()
        submitted = st.form_submit_button("添加")
        if submitted:
            if not code:
                st.error("请输入代码")
            elif add_contract(code):
                st.success(f"已添加：{code}")
                st.rerun()
            else:
                st.warning("已存在或代码格式不正确（支持 IF/IH/IC/IM 开头）")

    st.divider()

    contracts = get_all()
    if contracts:
        st.subheader("已保存的")
        for c in contracts:
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{c['code']}** — {c['name']}")
            if col2.button("删除", key=f"del_{c['code']}"):
                delete_contract(c["code"])
                st.rerun()
    else:
        st.info("还没有内容，请在左侧添加。")

# ── 主区域 ──
contracts = get_all()
if len(contracts) < 2:
    st.info("请先在左侧添加至少 2 个。")
    st.stop()

codes = [c["code"] for c in contracts]

# 刷新按钮
st.button("刷新价格", type="primary", use_container_width=True)

# ── 指数行情 ──
idx_cols = st.columns(2)
m_val = get_index_price("sh000852")
c_val = get_index_price("sh000905")
idx_cols[0].metric(label="M 数值", value=f"{m_val:,.2f}" if m_val is not None else "获取失败")
idx_cols[1].metric(label="C 数值", value=f"{c_val:,.2f}" if c_val is not None else "获取失败")

# ── 差价计算（4 组） ──
all_codes = []
diff_pairs = []
col_holders = []

labels = ["M次月差价", "M次季差价", "C次月差价", "C次季差价"]
for i in range(4):
    st.subheader(labels[i])
    cols = st.columns(5)
    with cols[0]:
        a = st.selectbox(f"A", codes, index=0, key=f"diff_{i}_a")
    with cols[1]:
        b = st.selectbox(f"B", codes, index=min(1, len(codes) - 1), key=f"diff_{i}_b")
    diff_pairs.append((a, b))
    col_holders.append(cols)
    all_codes.extend([a, b])

# 批量获取价格
prices = batch_get_prices(list(dict.fromkeys(all_codes)))

# 填充前4组的结果
diff_results = []
for i, (a, b) in enumerate(diff_pairs):
    pa, pb = prices.get(a), prices.get(b)
    cols = col_holders[i]
    cols[2].metric(label=f"{a.replace('IM', 'M', 1).replace('IC', 'C', 1)} 最新价", value=f"{pa:,.2f}" if pa is not None else "获取失败")
    cols[3].metric(label=f"{b.replace('IM', 'M', 1).replace('IC', 'C', 1)} 最新价", value=f"{pb:,.2f}" if pb is not None else "获取失败")
    if pa is not None and pb is not None:
        d = pa - pb
        cols[4].metric(label=f"差值", value=f"{d:+,.2f}")
        diff_results.append(d)
    else:
        cols[4].metric(label="差值", value="--")
        diff_results.append(None)

# ── 计算跨品种差价（差价5、6） ──
cross_labels = ["M-C次月差值", "M-C次季差值"]
cross_indices = [(0, 2), (1, 3)]  # diff_results 中的索引
SPACER = "<div style='height: 28px'></div>"
for idx, (i, j) in enumerate(cross_indices):
    st.subheader(cross_labels[idx])
    cols = st.columns(5)
    cols[0].markdown(SPACER, unsafe_allow_html=True)
    cols[1].markdown(SPACER, unsafe_allow_html=True)
    cols[2].markdown(SPACER, unsafe_allow_html=True)
    cols[3].markdown(SPACER, unsafe_allow_html=True)
    if diff_results[i] is not None and diff_results[j] is not None:
        val = diff_results[i] - diff_results[j]
        cols[4].metric(label=f"跨品种差值", value=f"{val:+,.2f}")
    else:
        cols[4].metric(label="跨品种差值", value="--")
