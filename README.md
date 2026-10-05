# confluence-doc スキル

社内資料をConfluenceの子ページ「【Claude案】〇〇」に書く Claude Code スキル。
元にしたページ：[書き方ルール](https://techouse.atlassian.net/wiki/spaces/~5eaa6a7b7dab3a0bb4fb5d8e/pages/6164579270/Claude) / [表最適化マニュアル](https://techouse.atlassian.net/wiki/spaces/~5eaa6a7b7dab3a0bb4fb5d8e/pages/6147375283)

## 入れ方

```bash
mkdir -p ~/.claude/skills && cp -r skills/confluence-doc ~/.claude/skills/
```

使うときは `/confluence-doc` に #お願い・#メモ・#データ元 を付けて頼む（「議事録にまとめて」などでも起動する）。

## 中身

- `skills/confluence-doc/SKILL.md`：起動する言い方、依頼の形、手順、報告の形
- `skills/confluence-doc/references/`：共通ルール（書き方ルールの(2)(3)(5)）と表最適化マニュアル
- `skills/confluence-doc/formats/`：8種類の型（「よくある直し」に指摘を日付つきで足して育てる）
- `skills/confluence-doc/scripts/colwidth.py`：列幅の計算・折り返しの確認
- `skills/confluence-doc/scripts/check_page.py`：書き込み前のHTMLのチェック
- `trial/`：試しに作った議事録（9/30 人材紹介DIV定例。Confluenceには未投稿）
