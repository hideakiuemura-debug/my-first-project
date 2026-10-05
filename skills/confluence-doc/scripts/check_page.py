#!/usr/bin/env python3
"""書き込む前のHTMLを、書き方ルールの機械で確かめられる部分についてチェックする。

使い方
  python3 check_page.py page.html --title "【Claude案】【議事録】人材紹介DIV定例_2026/09/30"
  python3 check_page.py page.html --title "…" --meeting   # 会議で使う資料（末尾に h2「議事録」が要る）

見ること
  並び（青枠→目次→本文→(n)参考資料→要確認リスト→議事録）、青枠の最後の1行と件数、
  要確認リストの3列と【出す前】【当日】、【要確認｜理由】→ アクションとオレンジ太字、
  食い違いのA/Bリンク、各表の列幅と折り返し（colwidth.py）、1表8行、セルの br/ul/空p、
  使わない言葉、1文60字、箇条書き5項目、タイトルの長さ
見ないこと（人が読んで確かめる）
  中身の正しさ、14観点の指摘の重さ、推奨が1つか、太字の使いすぎ、行末の1〜2文字（本文）
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from colwidth import report  # noqa: E402

ORANGE = '#ff991f">'
NG_WORDS = ["前期", "今期", "次期", "来期", "決めてほしい", "求める", "してほしい", "する形", "と報告された", "出典", "<time", "【サンプル】"]


def strip(s):
    return re.sub(r"<[^>]+>", "", s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--title", required=True)
    ap.add_argument("--meeting", action="store_true", help="会議で使う資料（h2「議事録」が要る）")
    a = ap.parse_args()
    h = open(a.html, encoding="utf-8").read()
    ng = []

    # 並び
    seq = [b[0] or b[1] for b in re.findall(r'<div data-type="(panel-info|extension)"|<h2>(.*?)</h2>', h)]
    print("並び:", " → ".join(seq))
    if seq[:2] != ["panel-info", "extension"]:
        ng.append("一番上が 青枠 → 目次 になっていない")
    h2 = [s for s in seq if s not in ("panel-info", "extension")]
    ref = [i for i, s in enumerate(h2) if re.fullmatch(r"\(\d+\) 参考資料", s)]
    if not ref:
        ng.append("「(n) 参考資料」がない")
    else:
        tail = h2[ref[0] + 1:]
        want = ["要確認リスト", "議事録"] if a.meeting else ["要確認リスト"]
        if tail != want:
            ng.append(f"下部の並びが違う: {tail}（正：{want}）")
        if len(h2[:ref[0]]) > 7:
            ng.append("大見出しが7つを超える")
    if a.meeting and "<h2>議事録</h2>" in h:
        mins = h.split("<h2>議事録</h2>")[1]
        if re.findall(r"<h3>(.*?)</h3>", mins)[:4] != ["サマリ", "決定事項", "アクション", "議事録"]:
            ng.append("議事録の h3 が サマリ/決定事項/アクション/議事録 になっていない")

    # 要確認
    if "<h2>要確認リスト</h2>" not in h:
        ng.append("h2「要確認リスト」がない")
        main_part, lst = h, ""
    else:
        main_part, rest = h.split("<h2>要確認リスト</h2>", 1)
        lst = rest.split("<h2>")[0]
        if 'data-type="panel-warning"' not in lst:
            ng.append("要確認リストの下に黄枠がない")
    m = re.search(r"要確認は(\d+)件（うち出す前に埋めるのは(\d+)件）。末尾の要確認リストを見て、親ページを直してください</p></div>", h)
    if not m:
        ng.append("青枠の最後の1行「要確認はn件（うち出す前に埋めるのはm件）。…」がない")
    rows = re.findall(r"<tr>(.*?)</tr>", lst, re.S)
    n = pre = tou = 0
    if rows:
        hdr = [strip(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", rows[0], re.S)]
        if hdr != ["箇所", "指摘", "アクション"]:
            ng.append(f"要確認リストの列が {hdr}（正：箇所/指摘/アクション。No・理由の列は付けない）")
        body = rows[1:]
        n = len(body)
        pre = sum("【出す前】" in r for r in body)
        tou = sum("【当日】" in r for r in body)
        if pre + tou != n:
            ng.append("指摘の頭に【出す前】か【当日】がない行がある")
        if ORANGE in lst:
            ng.append("要確認リストのアクション列はオレンジにしない")
    if m and (int(m.group(1)), int(m.group(2))) != (n, pre):
        ng.append(f"件数が合わない（青枠 {m.group(1)}件/出す前{m.group(2)}件、表 {n}行/出す前{pre}行）")
    inline = re.findall(r'#ff991f">(【要確認｜.*?)</span>', main_part, re.S)
    cells = main_part.count(ORANGE + "【要確認】<")
    print(f"要確認: 青枠{m.groups() if m else '—'} / リスト{n}行（出す前{pre}・当日{tou}）/ 本文の【要確認｜…】{len(inline)}か所 / セルの【要確認】{cells}個")
    if len(inline) + (1 if cells else 0) > n:
        ng.append("本文の【要確認】より要確認リストの行が少ない（取りこぼし？）")
    for s in inline:
        if "→" not in s:
            ng.append(f"「→ アクション」がない: {strip(s)[:30]}")
        if "食い違い" in s and len(re.findall(r"<a ", s)) < 2:
            ng.append(f"食い違いにAとBのリンクがない: {strip(s)[:30]}")
    if re.search(r'(?<!<strong>)<span style="color: #ff991f">', main_part):
        ng.append("【要確認】のオレンジが太字（<strong>）で包まれていない")

    # 表
    for dw, tb in re.findall(r'<table data-width="(\d+)">(.*?)</table>', h, re.S):
        trs = re.findall(r"<tr>(.*?)</tr>", tb, re.S)
        cl = [re.findall(r"<t[hd]([^>]*)>(.*?)</t[hd]>", r, re.S) for r in trs]
        if any("data-colwidth" not in attr for r in cl for attr, _ in r):
            ng.append("data-colwidth の付け忘れ")
            continue
        widths = [int(re.search(r'data-colwidth="(\d+)"', attr).group(1)) for attr, _ in cl[0]]
        txt = [[strip(c) for _, c in r] for r in cl]
        out = report(txt, widths, data_width=int(dw))
        print(f"--- 表「{'/'.join(txt[0])}」{len(trs) - 1}行")
        print(out)
        big = txt[0] == ["箇所", "指摘", "アクション"] or txt[0][:2] == ["種別", "プロジェクト"] or "観点" in txt[0]
        if len(trs) - 1 > 8 and not big:
            ng.append(f"1表8行を超える: {txt[0]}")
        if "!!" in out:
            ng.append(f"列幅の合計が範囲外: {txt[0]}")
        for line in out.splitlines():
            if "削るか広げる" in line or "見出しは" in line or "1列目は" in line:
                ng.append(f"折り返し: {txt[0]} {line.strip()}")
        if re.search(r"<br|<ul|<p></p>", tb):
            ng.append(f"セルに <br>/<ul>/空<p>: {txt[0]}")

    # 文体
    for w in NG_WORDS:
        if w in h:
            ng.append(f"使わない言葉: {w}")
    plain = re.sub(r"<[^>]+>", "\n", h)
    for sent in re.split(r"[。\n]", plain):
        s = sent.strip()
        if len(s) > 60 and "食い違い" not in s:
            ng.append(f"1文60字超（{len(s)}字）: {s[:30]}…")
    for ul in re.findall(r"<ul>(.*?)</ul>", h, re.S):
        if ul.count("<li>") > 5 and "問い" not in ul:
            ng.append("箇条書きが5項目を超える")
    if "<p></p>" in h:
        ng.append("空の <p> がある")

    # タイトル
    t = a.title.replace("【Claude案】", "")
    tl = sum(0.5 if c.isascii() else 1 for c in t)
    print(f"タイトル「{a.title}」 {tl:g}字（【Claude案】は数えない）")
    if not a.title.startswith("【Claude案】【"):
        ng.append("タイトルが【Claude案】【種類】で始まっていない")
    if tl > 25:
        ng.append("タイトルが全角25字を超える")

    print("\n=== NG ===" if ng else "\n=== NGなし（中身・14観点・推奨・太字は人が読んで確かめる）===")
    for x in ng:
        print("・" + x)
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    main()
