---
name: confluence-doc
description: 社内資料をConfluenceに書くスキル。出力先ページの子ページ「【Claude案】〇〇」に、書き方ルールと表最適化マニュアルどおりの資料を作る。8種類（定例資料・壁打ち/相談・検討資料・企画書・方針/計画・振り返り・議事録・マニュアル）に対応。「定例資料を作って」「議事録にまとめて」「振り返りを書いて」「企画書にして」「検討資料」「壁打ち資料」「方針・計画」「マニュアルにして」「Confluenceに資料を書いて」「/confluence-doc」や、#お願い・#メモ・#データ元 の形の依頼で使う。
---

# confluence-doc

社内資料をConfluenceに書く。資料の完成は「上位者が承認か否認だけで決められる状態」。

## ファイル

| ファイル | 中身 | いつ読むか |
|---|---|---|
| references/writing-rules.md | 共通ルール（書き方ルールの(2)(3)(5)） | 毎回、書く前に全部 |
| references/table-optimization.md | 表最適化マニュアル | 毎回、表を書く前に全部 |
| formats/*.md | 種類ごとの型と「よくある直し」 | 種類が決まったら該当の1つ |
| scripts/colwidth.py | 列幅の計算・折り返しの確認 | 表を1つ書くたびに |
| scripts/check_page.py | 書き込み前のHTMLのチェック（並び・件数・列幅・文体） | 書き込む直前に |

種類 → 型ファイル：定例資料 `teirei.md`／壁打ち・相談 `kabeuchi.md`／検討資料 `kentou.md`／企画書 `kikakusho.md`／方針・計画 `houshin.md`／振り返り `furikaeri.md`／議事録 `gijiroku.md`／マニュアル `manual.md`

元ページ（ルールの正。食い違ったら元ページに合わせ、references を直す）
- 書き方ルール：https://techouse.atlassian.net/wiki/spaces/~5eaa6a7b7dab3a0bb4fb5d8e/pages/6164579270/Claude
- 表最適化マニュアル：https://techouse.atlassian.net/wiki/spaces/~5eaa6a7b7dab3a0bb4fb5d8e/pages/6147375283

## 依頼の形

```
#お願い
（種類と出力先。例：議事録にまとめて。9/30の人材紹介DIV定例。出力先：ConfluenceのURL）

#メモ
・（伝えたいこと・自分の考え・決まっていること・期間・範囲・読み手）

#データ元
（リンクを1行に1つ。タグ【数値】【中身】【一覧】【前回】【見本】【貼り付け】は任意）
```

#書き方 は書かれていなくてよい（このスキルのルールに従う）。形が崩れていても、中身から読み取る。

## 手順

### 1. ルールを読む

`references/writing-rules.md` と `references/table-optimization.md` を全部読む。種類が決まったら `formats/<種類>.md` を読み、「よくある直し」を必ず守る。

### 2. 足りない情報を選択式で聞く（書く前に）

書き始めるのに要る4つ：**種類・出力先・対象期間・データ元**。依頼から読み取れないものだけを AskUserQuestion で聞く。

- 1回に3問まで。選択肢は2〜4個（「その他」は自動で付く）。推奨があれば先頭に置き「(推奨)」
- 4つとも足りないときは、種類・出力先・対象期間を先に聞き、データ元は次の回に回す
- 種類：8種類から、依頼文に近いものを2〜4個
- 出力先：依頼文や会話に出たConfluenceページ、データ元の親ページなどを候補に
- 対象期間：会議日・月・Q など、データ元の日付から候補を作る
- **#データ元がなければ**、Confluenceを検索して候補を選択式で示す（multiSelect: true）
  - `searchConfluenceUsingCql` で、タイトル・本文のキーワード、対象期間（`lastmodified` / `created`）、出力先と同じスペースで絞る
  - 例：`title ~ "人材紹介DIV定例" AND type = page AND lastmodified >= "2026-09-01" ORDER BY lastmodified DESC`
  - 候補は「タイトル（更新日）」で、説明にスペース名と1行の中身
- 書き始めてから見つかった細かい抜けは質問せず、本文に【要確認｜理由】→ アクションで書く

### 3. 元資料をすべて読む

- Confluence は `getConfluencePage`（cloudId は `techouse.atlassian.net`、本文は `markdown` で読む）。本文中のリンクは1階層だけ辿る
- 【一覧】の親ページは `getConfluencePageDescendants` で子を出し、対象期間に更新された子だけ読む
- スプレッドシート・Drive は Google Drive の道具で読む。読めなければ別の値で代えず【要確認｜未読】→「シートの要点を貼ってもらう」
- Slack は読むだけ（書き込まない）
- 読めなかった元資料は控えておき、最後に報告する
- 会議の前の資料（定例資料・検討資料）では、会議の後の情報を使わない

### 4. 突合する

数値・日付・固有名詞・発言の出どころを確かめる。内訳の和・率×母数・目標−実績は計算し直す。食い違いはAとBの名前・URL・それぞれの値を控える。

### 5. 書く

**並び（必ずこの順）**

1. 青枠（`panel-info`）：結論1〜2文。最後の1行は「要確認はn件（うち出す前に埋めるのはm件）。末尾の要確認リストを見て、親ページを直してください」
2. 目次（toc マクロ、大見出しだけ＝h2）
3. 本文（型ファイルの見出しどおり。大見出しは h2「(1) 〇〇」）
4. h2「(n) 参考資料」
5. h2「要確認リスト」（番号なし）：黄枠（`panel-warning`）の1文 → 表（箇所／指摘／アクション の3列。**No列・理由列は付けない**）
6. h2「議事録」：会議で使う資料（定例資料は必須、検討資料・壁打ち・相談は会議があれば）だけ。h3 サマリ／決定事項／アクション／議事録。会議前は各（当日記入）。種類が「議事録」の資料には置かない

**HTMLの骨組み**（`createConfluencePage` の contentFormat は `html`。初回は `getContentFormatGuide` を読む）

```html
<div data-type="panel-info"><p><strong>結論1〜2文。</strong><br>要確認はn件（うち出す前に埋めるのはm件）。末尾の要確認リストを見て、親ページを直してください</p></div>
<div data-type="extension" data-extension-key="toc" data-extension-type="com.atlassian.confluence.macro.core" data-parameters='{"macroParams":{"minLevel":{"value":"2"},"maxLevel":{"value":"2"}},"macroMetadata":{"schemaVersion":{"value":"1"},"title":"目次"}}'></div>
<h2>(1) 〇〇</h2>
<p>表の上のサマリ1文（太字にしない）。</p>
<table data-width="760"><thead><tr><th data-colwidth="…"><p>…</p></th>…</tr></thead><tbody>…</tbody></table>
<p>※注記<br>参照：<a href="URL">短いリンク名</a></p>
<hr>
…
<h2>(n) 参考資料</h2>
<ul><li><p><a href="URL" data-card-appearance="inline"></a></p></li></ul>
<hr>
<h2>要確認リスト</h2>
<div data-type="panel-warning"><p>本文の【要確認】n件と、上位者に突っ込まれる観点の指摘。アクションを進め、親ページを直す。</p></div>
<table data-width="760">…箇所／指摘／アクション…</table>
<hr>
<h2>議事録</h2>  <!-- 会議で使う資料だけ -->
<h3>サマリ</h3><p>（当日記入）</p><h3>決定事項</h3><p>（当日記入）</p><h3>アクション</h3><p>（当日記入）</p><h3>議事録</h3><p>（当日記入）</p>
```

**【要確認】の書き方**

- 抜けている箇所そのものに、アクションまで同じ太字・オレンジ：
  `<strong><span style="color: #ff991f">【要確認｜担当が未定】→ 狩野さんに確認する</span></strong>`
- 表のセルの中は `<strong><span style="color: #ff991f">【要確認】</span></strong>` だけ。指摘とアクションは要確認リストへ
- 食い違いは出てくるその場で、AとBの名前そのものをリンクにする：
  `【要確認｜食い違い】→ <a href="AのURL">A</a>と<a href="BのURL">B</a>で食い違い（Aは〇〇、Bは〇〇）。当日にどちらを正とするか決める`
  表のセルでは「<a>A</a>と<a>B</a>で食い違い」（リンク付き）だけ書き、（Aは〇〇、Bは〇〇）は表の直下の注記と要確認リストへ

**要確認リストの作り方**

1. 本文の【要確認】をすべて入れる（1か所に2つの抜けは1行にまとめ、本文と件数をそろえる）
2. 「上位者に突っ込まれる観点」14個を、どの種類の資料にも**全部**掛ける。型ファイルの「特に効く観点」は念入りに。そのうち重要なものだけを入れる（個数の上限なし）
3. 「指摘」の頭に【出す前】か【当日】。会議で決める論点の担当・期限などは【当日】
4. 箇所は「(2) 決定事項」「(5) 議題③」のように節番号つきで短く。アクション列は普通の文字
5. 青枠の件数 n（とm）を、表の行数とそろえる

**表を1つ書くたびに列幅を計算する**

```bash
python3 ~/.claude/skills/confluence-doc/scripts/colwidth.py - --text 1 <<'JSON'
[["箇所","指摘","アクション"],["(3) ToDo","【当日】期限が記録にない","当日に期限を決める"]]
JSON
```

- 出た `data-colwidth` を全セル（見出し行も）に付ける。合計は740〜755
- 折り返しの警告が出たら、まず文字を削る（全角記号→半角、語尾を削る）。削れなければ列を配り直す。2行目に1〜2文字だけ残る行は必ず直す
- 中身を1セルでも変えたら計算し直す

### 6. チェックしてから書き込む

本文のHTMLをファイルに保存し、機械で見られる部分を確かめる。NGが0になるまで直す。

```bash
python3 ~/.claude/skills/confluence-doc/scripts/check_page.py page.html --title "【Claude案】【議事録】…"   # 会議で使う資料は --meeting
```

そのうえで、`references/writing-rules.md` の「書き込み前のチェック」と、`references/table-optimization.md` §8 の自己チェックを全部通す（中身の正しさ・14観点・推奨が1つか・太字は人の目で）。

### 7. 子ページに書き込む

- 出力先ページは**書き換えない**。`createConfluencePage` で `parentId` = 出力先ページID、`spaceId` = 出力先のスペースで子ページを作る
- タイトル：`【Claude案】【種類】対象_期間`（例：【Claude案】【議事録】人材紹介DIV定例_2026/09/30）。【サンプル】は付けない
- 同じタイトルの子ページが既にあるときは、直前に最新版を取り直してから `updateConfluencePage` で更新する（新しく作らない）
- 子ページ以外のページは書き換えない。Slack は読むだけ

## 報告の形（書き終えたらチャットに返す）

```
子ページ：<URL>
読めなかった元資料：<なし／リンクと理由>
要確認（特に重要なもの）：
・【出す前】…
・【当日】…
元資料の間の食い違い：<なし／[A](URL)と[B](URL)で食い違い（Aは〇〇、Bは〇〇）>
```

## 指摘をもらったら（スキルを育てる）

作業中・作業後に資料の直しを指摘されたら、直したうえで、その種類の `formats/<種類>.md` の「よくある直し」に日付つきで1行足す。

```
- 2026-10-05：ToDoの期限が記録にないときは、セルを【要確認】にして要確認リストへ（期限を推測で埋めない）
```

- 全種類に効く指摘は `references/writing-rules.md` の該当の節に足し、末尾に「（2026-10-05 追記）」
- 列幅・文字幅の指摘（実際に折れた／収まった）は `references/table-optimization.md` に実例を足し、必要なら `scripts/colwidth.py` の値を直す
- 元ページ（Confluence）は書き換えない。元ページにも反映したほうがよい指摘は、報告の最後に「元ページに入れる候補」として挙げる
