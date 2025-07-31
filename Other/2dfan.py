import argparse
import json
import sys
import time
from pathlib import Path
from tqdm import tqdm

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from openpyxl import Workbook

def scrape_2dfan_month(year: int, month: int):
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
        time.sleep(0.5)  # polite delay

    driver.quit()
    return rows

def query_vndb(name: str):
    payload = {
        "filters": ["search", "=", name],
        "fields": "id,title,alttitle",
        "sort": "title",
        "reverse": True,
        "page": 1,
        "results": 20,
    }
    r = requests.post(
        "https://api.vndb.org/kana/vn",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def choose_result(src_title: str, candidates: list):
    print(f"\n{src_title} 有多条匹配结果，请选择（0 = 跳过）：")
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


def enrich_with_vndb(rows: list):
    cached = {}
    for idx, row in enumerate(tqdm(rows, ncols=150)):
        src_title = row["title"]
        try:
            cached[idx] = query_vndb(src_title)
        except Exception as ex:
            print(f"[{src_title}] 查询出错: {ex}", file=sys.stderr)
            cached[idx] = []

    out_rows = []
    for idx, row in enumerate(rows):
        src_title = row["title"]
        results = cached.get(idx, [])

        if len(results) == 1:
            sel = results[0]
        elif len(results) == 0:
            sel = None
            print(f"{src_title} VNDB 无结果")
        else:
            sel = choose_result(src_title, results)

        if sel:
            if sel.get("alttitle"):
                alttitle_val = sel["alttitle"]
                title_val = sel["title"]
            else:
                alttitle_val = sel["title"]
                title_val = ""
            vndb_url_val = f"https://vndb.org/{sel['id']}"
        else:
            alttitle_val = src_title
            title_val = ""
            vndb_url_val = ""

        out_rows.append(
            {
                "alttitle": alttitle_val,
                "title": title_val,
                "2dfan_url": row["2dfan_url"],
                "vndb_url": vndb_url_val,
            }
        )

    return out_rows

def export_to_xlsx(rows: list, path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "subjects"

    ws.append(["alttitle", "title", "2dfan_url", "vndb_url"])

    for r in rows:
        ws.append([r["alttitle"], r["title"], r["2dfan_url"], r["vndb_url"]])

    wb.save(path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int)
    ap.add_argument("month", type=int)
    args = ap.parse_args()

    print(f"2DFan {args.year}-{args.month:02d}")
    base_rows = scrape_2dfan_month(args.year, args.month)
    print(f"共抓到 {len(base_rows)} 条")

    merged_rows = enrich_with_vndb(base_rows)

    out_path = Path(f"subjects_{args.year}_{args.month:02d}.xlsx")
    export_to_xlsx(merged_rows, out_path)