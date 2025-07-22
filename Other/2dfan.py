
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_2dfan_month(year, month):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 12)
    driver.get(f"https://2dfan.com/subjects/incoming/{year}/{month:02d}")

    rows = []
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#subjects .media-body h4 a")))
        for a in driver.find_elements(By.CSS_SELECTOR, "#subjects .media-body h4 a"):
            rows.append({"title": a.text.strip(), "2dfan_url": a.get_attribute("href")})

        nxt = driver.find_elements(By.CSS_SELECTOR, ".pagination a[rel='next']")
        if not nxt:
            break
        nxt_href = nxt[0].get_attribute("href")
        if not nxt_href or nxt_href == driver.current_url:
            break
        driver.get(nxt_href)
        time.sleep(0.8)
    driver.quit()
    return pd.DataFrame(rows)

def query_vndb(name):
    payload = {
        "filters": ["search", "=", name],
        "fields": "id,title,alttitle,developer",
        "sort": "title",
        "reverse": True,
        "page": 1,
        "results": 20
    }
    r = requests.post("https://api.vndb.org/kana/vn", headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])

def choose_result(src_title, candidates):
    print(f"\n【{src_title}】 有多条匹配结果，请选择（0 = 跳过）：")
    for idx, c in enumerate(candidates, 1):
        at = c.get("alttitle") or "-"
        print(f"  {idx}. {c['title']}  |  别名: {at}  |  id: {c['id']}")
    while True:
        sel = input("输入序号：").strip()
        if sel.isdigit():
            sel = int(sel)
            if sel == 0:
                return None
            if 1 <= sel <= len(candidates):
                return candidates[sel - 1]
        print("无效输入，请重新输入。")

def enrich_with_vndb(df: pd.DataFrame) -> pd.DataFrame:
    out_rows = []
    for _, row in df.iterrows():
        src_title = row["title"]                 # 2DFan 抓到的标题（默认当 alttitle）
        try:
            results = query_vndb(src_title)
        except Exception as ex:
            print(f"[{src_title}] 查询出错: {ex}", file=sys.stderr)
            results = []

        if len(results) == 1:
            sel = results[0]
        elif len(results) == 0:
            sel = None
            print(f"[{src_title}] VNDB 无结果")
        else:
            sel = choose_result(src_title, results)   # 交互选择

        # ====== 新的列赋值规则 ======
        if sel:                                      # 有匹配
            if sel.get("alttitle"):                  # ▶ 有 alttitle
                alttitle_val = sel["alttitle"]
                title_val    = sel["title"]
            else:                                    # ▶ 只有 title
                alttitle_val = sel["title"]
                title_val    = ""            # ← 改成空串
            vndb_url_val = f"https://vndb.org/{sel['id']}"
        else:                                        # 无匹配 / 跳过
            alttitle_val = src_title
            title_val    = ""                # ← 改成空串
            vndb_url_val = ""

        out_rows.append({
            "alttitle":  alttitle_val,
            "title":     title_val,
            "2dfan_url": row["2dfan_url"],
            "vndb_url":  vndb_url_val
        })

    return pd.DataFrame(out_rows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int)
    ap.add_argument("month", type=int)
    args = ap.parse_args()

    print(f"== 抓取 2DFan {args.year}-{args.month:02d} ==")
    base_df = scrape_2dfan_month(args.year, args.month)
    print(f"  · 共抓到 {len(base_df)} 条")

    print("\n== 查询 VNDB ==")
    merged_df = enrich_with_vndb(base_df)

    out_path = Path(f"subjects_{args.year}_{args.month:02d}.xlsx")
    merged_df.to_excel(out_path, index=False)
    print(f"\n✔ 已写出 {out_path.resolve()}")