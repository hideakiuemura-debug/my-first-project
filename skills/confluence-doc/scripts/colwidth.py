#!/usr/bin/env python3
"""Confluenceの表の列幅を中身から計算する。

文字幅（9/30に実機の折り返しで検証した値）
  全角16 / 数字9 / 英小文字8 / 英大文字11 / %&@ 13 / 記号( ) , . / - など5
  左右の余白24、列の最小40（No列は40）

使い方
  # 表をJSONで渡す（1行目が見出し）
  python3 colwidth.py table.json
  echo '[["箇所","指摘","アクション"],["(2) 決定事項","…","…"]]' | python3 colwidth.py -

  # Markdownの表でもよい
  python3 colwidth.py --md table.md

  # 文章列を指定する（0始まり。省略時は一番長い列）
  python3 colwidth.py table.json --text 1

  # 既にある列幅で折り返しを確かめる
  python3 colwidth.py table.json --widths 159,423,168

  # 1つの文字列の必要幅だけ見る
  python3 colwidth.py --measure "常時80%以上"

出力
  data-colwidth の値（合計は data-width より5〜20px小さく。760なら740〜755）
  折り返すセルと、2行目に1〜2文字だけ残るセルの警告
"""
import argparse
import json
import math
import re
import sys
import unicodedata

PAD = 24
MIN_COL = 40
NO_COL = 40  # No列は40pxで作れる（表最適化マニュアル §3-2）
ZEN = 16
WIDE_SYMBOLS = set("%&@")


def char_width(ch: str) -> int:
    if ch.isdigit() and ch.isascii():
        return 9
    if "a" <= ch <= "z":
        return 8
    if "A" <= ch <= "Z":
        return 11
    if ch in WIDE_SYMBOLS:
        return 13
    if ch.isascii():
        # ( ) , . / - : + ~ 空白 などの半角記号
        return 5
    if unicodedata.east_asian_width(ch) in ("F", "W", "A"):
        return ZEN
    # 半角カナなど
    return 8


def text_width(s: str) -> int:
    return sum(char_width(c) for c in s)


def need_width(s: str) -> int:
    """折り返さない列幅。"""
    return max(MIN_COL, text_width(s) + PAD)


def lines_in(s: str, col: int) -> tuple[int, int]:
    """(行数, 最終行の幅px)。最終行の幅が全角2字分以下なら行末残りの警告対象。"""
    inner = max(1, col - PAD)
    tw = text_width(s)
    if tw <= inner:
        return 1, tw
    n = math.ceil(tw / inner)
    last = tw - inner * (n - 1)
    return n, last


def is_no_col(rows, i) -> bool:
    """No列（見出しが No で、値が2桁までの数字）。実機で40pxに収まる。"""
    return strip_md(rows[0][i]) == "No" and all(re.fullmatch(r"\d{0,2}", strip_md(r[i])) for r in rows[1:])


def strip_md(s: str) -> str:
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # [名前](URL) → 名前
    s = re.sub(r"<[^>]+>", "", s)  # HTMLタグ
    s = s.replace("**", "").replace("__", "")
    return s.strip()


def parse_md(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [strip_md(c) for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def plan(rows, total, text_cols):
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    needs = [NO_COL if is_no_col(rows, i) else max(need_width(strip_md(r[i])) for r in rows) for i in range(ncol)]
    if not text_cols:
        text_cols = [max(range(ncol), key=lambda i: needs[i])]
    fixed = sum(needs[i] for i in range(ncol) if i not in text_cols)
    rest = total - fixed
    widths = list(needs)
    text_need = sum(needs[i] for i in text_cols)
    if rest >= text_need:
        # 余りは文章列へ（複数なら必要幅の比で配る）
        for i in text_cols:
            widths[i] = needs[i] + (rest - text_need) * needs[i] // text_need
    else:
        # 入りきらない：文章列は残りを必要幅の比で分ける（最小は全角4字分）
        for i in text_cols:
            widths[i] = max(88, rest * needs[i] // text_need)
    # 端数を最後の文章列で吸収して合計を total にそろえる
    widths[text_cols[-1]] += total - sum(widths)
    return rows, needs, widths, text_cols


def report(rows, widths, needs=None, text_cols=None, data_width=760):
    out = []
    s = sum(widths)
    out.append(f"data-width: {data_width}")
    out.append(f"data-colwidth: {' / '.join(map(str, widths))}（合計{s}）")
    lo, hi = data_width - 20, data_width - 5
    if not (lo <= s <= hi):
        out.append(f"!! 合計が{lo}〜{hi}の外です")
    header = rows[0]
    for i, w in enumerate(widths):
        mark = "（文章列）" if text_cols and i in text_cols else ""
        need = f" 必要{needs[i]}" if needs else ""
        per_line = (w - PAD) // ZEN
        out.append(f"  列{i} 「{strip_md(header[i])}」{mark}: {w}px{need} / 1行に全角{per_line}字")
    warns = []
    for r_i, row in enumerate(rows):
        for c_i, cell in enumerate(row):
            cell = strip_md(cell)
            if not cell or (is_no_col(rows, c_i) and widths[c_i] >= NO_COL):
                continue
            n, last = lines_in(cell, widths[c_i])
            where = "見出し" if r_i == 0 else f"{r_i}行目"
            if n >= 2:
                over = text_width(cell) - (widths[c_i] - PAD)
                msg = f"  {where} 列{c_i}: {n}行に折れる（必要{need_width(cell)}px）「{cell[:24]}」"
                if n == 2:
                    msg += f" あと約{math.ceil(over / ZEN)}字削れば1行"
                if last <= ZEN * 2:
                    msg += " ← 最終行に1〜2文字だけ残る。削るか広げる"
                if r_i == 0:
                    msg += " ← 見出しは1行に"
                elif c_i == 0 and not (text_cols and 0 in text_cols):
                    msg += " ← 1列目は1行に"
                warns.append(msg)
    if warns:
        out.append("折り返し:")
        out.extend(warns)
    else:
        out.append("折り返し: なし（全セル1行）")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?", help="JSONファイル（- で標準入力）")
    ap.add_argument("--md", help="Markdownの表のファイル")
    ap.add_argument("--text", help="文章列の番号（0始まり、カンマ区切り）")
    ap.add_argument("--widths", help="既存の列幅で確かめる（カンマ区切り）")
    ap.add_argument("--data-width", type=int, default=760)
    ap.add_argument("--total", type=int, help="列幅の合計（既定は data-width − 10）")
    ap.add_argument("--measure", help="文字列1つの必要幅を出す")
    a = ap.parse_args()

    if a.measure is not None:
        print(f"「{a.measure}」 必要幅 {need_width(a.measure)}px（文字{text_width(a.measure)}+余白{PAD}）")
        return

    if a.md:
        with open(a.md, encoding="utf-8") as f:
            rows = parse_md(f.read())
    elif a.src:
        raw = sys.stdin.read() if a.src == "-" else open(a.src, encoding="utf-8").read()
        rows = json.loads(raw)
        if isinstance(rows, dict):
            rows = rows["rows"]
    else:
        ap.error("表（JSON か --md）か --measure を渡してください")
    rows = [[str(c) for c in r] for r in rows]

    if a.widths:
        widths = [int(x) for x in a.widths.split(",")]
        print(report(rows, widths, data_width=a.data_width))
        return

    total = a.total or a.data_width - 10
    text_cols = [int(x) for x in a.text.split(",")] if a.text else []
    rows, needs, widths, text_cols = plan(rows, total, text_cols)
    print(report(rows, widths, needs, text_cols, a.data_width))


if __name__ == "__main__":
    main()
