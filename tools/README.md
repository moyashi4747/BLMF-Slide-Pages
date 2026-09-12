# tools/pdf2png.py

Google Slides から書き出したスライド PDF を、**連番の PNG（アルファチャンネルなし / RGB）** に変換します。

## セットアップ（初回のみ）

```powershell
pip install -r tools/requirements.txt
```

## 基本の使い方

```powershell
python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf
```

`Pre-event/png/Pre-BLMFVol7_01.png` … `_15.png` が **1280×960（4:3・RGB・アルファなし）** で出力されます。

ディレクトリを渡すと、その中の `*.pdf` をまとめて変換します。

```powershell
python tools/pdf2png.py Pre-event
```

## よく使うオプション

| オプション | 既定値 | 説明 |
|---|---|---|
| `-o, --output DIR` | `<PDFと同じ階層>/png` | 出力先ディレクトリ |
| `--width N` | `1280` | 出力幅 px |
| `--height N` | 自動 | 出力高さ px。省略するとページの比率から計算（4:3 なら 960） |
| `--fit MODE` | `contain` | 幅と高さの両方を指定して比率が合わないときの処理。`contain` / `cover` / `stretch` |
| `--bg COLOR` | `white` | 背景・余白の色。`white` / `#1E7A5F` / `255,255,255` |
| `--prefix STR` | PDF名 + `_` | ファイル名の接頭辞 |
| `--start N` | `1` | 連番の開始番号 |
| `--digits N` | 自動 | 連番の桁数。`0` でページ数から自動（15ページなら2桁） |
| `--supersample F` | `2.0` | 描画倍率。大きいほど綺麗だが遅い |
| `--no-annots` | off | 注釈を描画しない |
| `--dry-run` | off | 書き出さずに出力予定だけ表示 |

### 例

```powershell
# 幅だけ指定（高さは比率から自動 → 1920x1440）
python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf --width 1920

# 16:9 の枠に収める（4:3 なので左右に余白が入る）
python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf --width 1280 --height 720 --fit contain

# 余白をスライドと同じ緑にする
python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf --width 1280 --height 720 --bg "#3B8C6E"

# slide_001.png から始める
python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf --prefix slide_ --digits 3
```

## 仕様メモ

- レンダラは [pypdfium2](https://github.com/pypdfium2-team/pypdfium2)（PDFium）。外部コマンド（Poppler / Ghostscript / ImageMagick）は不要。
- 目標サイズの `--supersample` 倍で描画してから Lanczos で縮小するため、文字や図形のエッジが滑らかになります。
- 背景を不透明色で塗りつぶしてから描画し、保存時も必ず `RGB` に変換するので、**出力 PNG にアルファチャンネルは含まれません**。
- 同名ファイルは上書きされます。事前に `--dry-run` で確認できます。
