# BLMF-Slide-Pages

BLMFスライドシステム用 GitHub Pages。スライド画像を URL から直接参照するための配信リポジトリです。

## 構成

| パス | 内容 |
|---|---|
| `Pre-event/` | 事前告知スライド。PDF（元データ）と `png/`（配信用画像） |
| `Template/` | スライドテンプレート画像 |
| `test/` | 動作確認用画像 |
| `tools/` | PDF → 連番 PNG 変換ツール（[使い方](tools/README.md)） |

## 画像 URL

`https://moyashi4747.github.io/BLMF-Slide-Pages/<パス>` で参照できます。

```
https://moyashi4747.github.io/BLMF-Slide-Pages/Pre-event/png/Pre-BLMFVol7_01.png
https://moyashi4747.github.io/BLMF-Slide-Pages/Pre-event/png/Pre-BLMFVol7_02.png
...
https://moyashi4747.github.io/BLMF-Slide-Pages/Pre-event/png/Pre-BLMFVol7_15.png
```

画像は **1280×960（4:3）/ RGB / アルファチャンネルなし** の PNG です。

## スライドの更新手順

1. Google Slides から PDF を書き出し、対象ディレクトリ（例: `Pre-event/`）に置く
2. 変換する

   ```powershell
   pip install -r tools/requirements.txt   # 初回のみ
   python tools/pdf2png.py Pre-event
   ```

3. 生成された `png/` ごとコミットして push する

ページ数が変わるとファイルの連番も変わるため、参照側の枚数指定も合わせて更新してください。

## メモ

- ルートの `.nojekyll` は GitHub Pages の Jekyll 処理を無効化しています（静的ファイルをそのまま配信するため）。
- このリポジトリが public の場合、元の PDF も URL から取得できる状態になります。
