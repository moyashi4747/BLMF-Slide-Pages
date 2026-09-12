#!/usr/bin/env python3
"""Google Slides から書き出した PDF を連番 PNG に変換する。

既定では 4:3 のスライドを 1280x960 の RGB PNG (アルファなし) で出力する。

使い方:
    python tools/pdf2png.py Pre-event/Pre-BLMFVol7.pdf
    python tools/pdf2png.py Pre-event -o dist/pre-event
    python tools/pdf2png.py slides.pdf --width 1920            # 高さは比率から自動
    python tools/pdf2png.py slides.pdf --width 1280 --height 720 --fit contain
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pypdfium2 as pdfium
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    sys.exit(
        f"依存パッケージがありません ({exc.name})。\n"
        "  pip install -r tools/requirements.txt"
    )


FIT_MODES = ("contain", "cover", "stretch")


def parse_color(text: str) -> tuple[int, int, int]:
    """'white' / '#RRGGBB' / '#RGB' / 'R,G,B' を RGB タプルにする。"""
    named = {
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "gray": (128, 128, 128),
        "grey": (128, 128, 128),
    }
    key = text.strip().lower()
    if key in named:
        return named[key]
    if key.startswith("#"):
        hexpart = key[1:]
        if len(hexpart) == 3:
            hexpart = "".join(c * 2 for c in hexpart)
        if len(hexpart) != 6:
            raise argparse.ArgumentTypeError(f"色の指定が不正です: {text}")
        return tuple(int(hexpart[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    parts = key.replace(" ", "").split(",")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        rgb = tuple(int(p) for p in parts)
        if all(0 <= v <= 255 for v in rgb):
            return rgb  # type: ignore[return-value]
    raise argparse.ArgumentTypeError(f"色の指定が不正です: {text}")


def collect_pdfs(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(p for p in target.glob("*.pdf") if p.is_file())
    if target.is_file():
        return [target]
    raise FileNotFoundError(target)


def target_size(
    page_w: float, page_h: float, width: int | None, height: int | None
) -> tuple[int, int]:
    """指定された幅・高さからページごとの出力サイズを決める。"""
    if width and height:
        return width, height
    if width:
        return width, max(1, round(width * page_h / page_w))
    if height:
        return max(1, round(height * page_w / page_h)), height
    raise ValueError("--width か --height のどちらかは必要です")


def fit_image(
    img: Image.Image, size: tuple[int, int], mode: str, bg: tuple[int, int, int]
) -> Image.Image:
    """アスペクト比が合わない場合に contain / cover / stretch で size に収める。"""
    tw, th = size
    if img.size == (tw, th):
        return img
    if mode == "stretch":
        return img.resize((tw, th), Image.LANCZOS)

    sw, sh = img.size
    ratio = min(tw / sw, th / sh) if mode == "contain" else max(tw / sw, th / sh)
    scaled = img.resize((max(1, round(sw * ratio)), max(1, round(sh * ratio))), Image.LANCZOS)

    if mode == "cover":
        left = (scaled.width - tw) // 2
        top = (scaled.height - th) // 2
        return scaled.crop((left, top, left + tw, top + th))

    canvas = Image.new("RGB", (tw, th), bg)
    canvas.paste(scaled, ((tw - scaled.width) // 2, (th - scaled.height) // 2))
    return canvas


def convert(pdf_path: Path, args: argparse.Namespace) -> int:
    doc = pdfium.PdfDocument(pdf_path)
    n_pages = len(doc)
    if n_pages == 0:
        print(f"  ページがありません: {pdf_path.name}")
        return 0

    out_dir = args.output or pdf_path.parent / "png"
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = args.prefix if args.prefix is not None else f"{pdf_path.stem}_"
    digits = args.digits or max(2, len(str(args.start + n_pages - 1)))
    bg = args.bg
    fill = (*bg, 255)  # 不透明で塗るので pdfium は 3byte RGB を返す

    written = 0
    for index in range(n_pages):
        page = doc[index]
        page_w, page_h = page.get_size()
        tw, th = target_size(page_w, page_h, args.width, args.height)

        # 目標サイズ以上で描画してから縮小すると輪郭が綺麗に出る
        scale = max(tw / page_w, th / page_h) * args.supersample
        scale = min(scale, args.max_scale)

        bitmap = page.render(
            scale=scale,
            draw_annots=not args.no_annots,
            fill_color=fill,
            rev_byteorder=True,
        )
        img = bitmap.to_pil()
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA", "PA"):
                flat = Image.new("RGB", img.size, bg)
                flat.paste(img, mask=img.getchannel("A"))
                img = flat
            else:
                img = img.convert("RGB")

        img = fit_image(img, (tw, th), args.fit, bg)

        name = f"{prefix}{args.start + index:0{digits}d}.png"
        dest = out_dir / name
        if args.dry_run:
            print(f"  [dry-run] {dest}  {img.width}x{img.height}")
        else:
            img.save(dest, "PNG", optimize=True)
            print(f"  {dest.name}  {img.width}x{img.height}")
        written += 1

    doc.close()
    return written


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="スライド PDF を連番 PNG (アルファなし) に変換する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", type=Path, help="PDF ファイル、または PDF を含むディレクトリ")
    p.add_argument(
        "-o", "--output", type=Path, default=None,
        help="出力先ディレクトリ (既定: PDF と同じ階層の png/)",
    )
    p.add_argument("--width", type=int, default=1280, help="出力幅 px (既定: 1280)")
    p.add_argument(
        "--height", type=int, default=None,
        help="出力高さ px (既定: ページの比率から自動。4:3 なら 960)",
    )
    p.add_argument(
        "--fit", choices=FIT_MODES, default="contain",
        help="幅と高さの両方を指定して比率が合わない場合の処理 (既定: contain)",
    )
    p.add_argument(
        "--bg", type=parse_color, default=(255, 255, 255),
        help="背景・余白の色。white / #RRGGBB / R,G,B (既定: white)",
    )
    p.add_argument(
        "--prefix", default=None,
        help="ファイル名の接頭辞 (既定: PDF のファイル名 + '_')",
    )
    p.add_argument("--start", type=int, default=1, help="連番の開始番号 (既定: 1)")
    p.add_argument(
        "--digits", type=int, default=0,
        help="連番の桁数。0 でページ数から自動 (既定: 0)",
    )
    p.add_argument(
        "--supersample", type=float, default=2.0,
        help="描画倍率。大きいほど綺麗だが遅い (既定: 2.0)",
    )
    p.add_argument(
        "--max-scale", type=float, default=12.0,
        help="描画倍率の上限。巨大サイズ指定時のメモリ保護 (既定: 12.0)",
    )
    p.add_argument("--no-annots", action="store_true", help="注釈を描画しない")
    p.add_argument("--dry-run", action="store_true", help="書き出さずに結果だけ表示する")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.width is not None and args.width <= 0:
        args.width = None
    if args.height is not None and args.height <= 0:
        args.height = None
    if not args.width and not args.height:
        print("エラー: --width か --height のどちらかを正の値で指定してください", file=sys.stderr)
        return 2

    try:
        pdfs = collect_pdfs(args.input)
    except FileNotFoundError:
        print(f"エラー: 入力が見つかりません: {args.input}", file=sys.stderr)
        return 2

    if not pdfs:
        print(f"エラー: PDF が見つかりません: {args.input}", file=sys.stderr)
        return 2

    total = 0
    for pdf in pdfs:
        print(f"{pdf}")
        total += convert(pdf, args)

    verb = "確認" if args.dry_run else "出力"
    print(f"\n完了: {len(pdfs)} ファイル / {total} ページを{verb}しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
