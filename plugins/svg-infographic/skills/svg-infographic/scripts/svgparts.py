"""SVG インフォグラフィックの部品集。

使い方:
    import sys; sys.path.insert(0, "<このスキルのディレクトリ>/scripts")
    from svgparts import Slide, C

    s = Slide("図のタイトル", "図の内容を一文で（aria-label に入る）")
    s.header("スライドの見出し", "右上の補足（任意）")
    ...
    s.save("out.svg")      # はみ出しの疑いがあれば警告を出す
    s.render("out.png")    # Chrome 系のブラウザのヘッドレスモードで 2 倍解像度の PNG にする

CLI:
    python3 svgparts.py render in.svg out.png   # 既存の SVG を PNG にする

色・サイズ・太さは SKILL.md の規則に合わせてある。部品の見た目を変えるときは、この
ファイルを直して全部の図で揃える。
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
from xml.sax.saxutils import escape

FONT = "'Hiragino Sans', 'Yu Gothic UI', 'Noto Sans JP', system-ui, sans-serif"

# PNG への変換に使うブラウザの候補。上から順に探す。SVGPARTS_CHROME があればそれを使う。
_BROWSER_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
_BROWSER_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge"]


def find_browser():
    """PNG への変換に使うブラウザの実行ファイルを返す。見つからなければ例外。"""
    env = os.environ.get("SVGPARTS_CHROME")
    if env:
        if os.path.exists(env) or shutil.which(env):
            return env
        raise FileNotFoundError(f"SVGPARTS_CHROME に指定されたブラウザが見つからない: {env}")
    for p in _BROWSER_PATHS:
        if os.path.exists(p):
            return p
    for c in _BROWSER_COMMANDS:
        found = shutil.which(c)
        if found:
            return found
    raise FileNotFoundError(
        "Chrome・Chromium・Edge が見つからない。環境変数 SVGPARTS_CHROME にブラウザの実行ファイルのパスを入れる")


class C:
    """色。役割は SKILL.md の色の表を参照。"""
    PRIMARY = "#2563EB"
    PRIMARY_BG = "#EFF6FF"
    ORANGE = "#F97316"     # 問題点・注目点
    ORANGE_BG = "#FFF7ED"
    ORANGE_LINE = "#FDBA74"
    GREEN = "#10B981"      # 完了・到達点
    GREEN_BG = "#ECFDF5"
    BG = "#F8FAFC"
    CARD = "#FFFFFF"
    LINE = "#E2E8F0"
    TEXT = "#1E293B"
    SUB = "#64748B"
    ARROW = "#94A3B8"


# アイコン。24×24 の格子に線で描く。"CUR" は描画時に線の色に置き換える（塗りつぶす点など）。
# 形は自作。種類を増やすときも、線だけ・角は丸く・格子の 2〜22 の内側に収める。
ICONS = {
    "user": ['<circle cx="12" cy="8" r="4"/>',
             '<path d="M4,21 C4,16.6 7.6,14 12,14 C16.4,14 20,16.6 20,21"/>'],
    "users": ['<circle cx="9" cy="8" r="3.5"/>',
              '<path d="M2.5,20 C2.5,16.2 5.4,14 9,14 C12.6,14 15.5,16.2 15.5,20"/>',
              '<path d="M15,4.8 A3.5,3.5 0 0 1 15,11.6"/>',
              '<path d="M17.5,14.4 C20,15.2 21.5,17.3 21.5,20"/>'],
    "building": ['<rect x="4" y="3" width="16" height="18" rx="1.5"/>',
                 '<path d="M8,7.5 H10 M14,7.5 H16 M8,11.5 H10 M14,11.5 H16 M10,21 V16.5 H14 V21"/>'],
    "server": ['<rect x="3" y="4" width="18" height="7" rx="2"/>',
               '<rect x="3" y="13" width="18" height="7" rx="2"/>',
               '<circle cx="7" cy="7.5" r="0.9" fill="CUR" stroke="none"/>',
               '<circle cx="7" cy="16.5" r="0.9" fill="CUR" stroke="none"/>',
               '<path d="M11,7.5 H17 M11,16.5 H17"/>'],
    "database": ['<ellipse cx="12" cy="5.5" rx="8" ry="3"/>',
                 '<path d="M4,5.5 V18.5 C4,20.2 7.6,21.5 12,21.5 C16.4,21.5 20,20.2 20,18.5 V5.5"/>',
                 '<path d="M4,12 C4,13.7 7.6,15 12,15 C16.4,15 20,13.7 20,12"/>'],
    "laptop": ['<rect x="4.5" y="5" width="15" height="10.5" rx="1.5"/>',
               '<path d="M2,19 H22"/>'],
    "ai": ['<rect x="6" y="6" width="12" height="12" rx="2"/>',
           '<rect x="9.5" y="9.5" width="5" height="5" rx="1"/>',
           '<path d="M9.5,2.5 V6 M14.5,2.5 V6 M9.5,18 V21.5 M14.5,18 V21.5 '
           'M2.5,9.5 H6 M2.5,14.5 H6 M18,9.5 H21.5 M18,14.5 H21.5"/>'],
    "container": ['<path d="M12,2.5 L20.5,7 V17 L12,21.5 L3.5,17 V7 Z"/>',
                  '<path d="M3.5,7 L12,11.5 L20.5,7 M12,11.5 V21.5"/>'],
    "wallet": ['<path d="M5,7 L15.5,3.5 L16.5,7"/>',
               '<rect x="3" y="7" width="18" height="13" rx="2"/>',
               '<path d="M21,11.5 H17 A2,2 0 0 0 17,15.5 H21"/>'],
    "coin": ['<circle cx="12" cy="12" r="9"/>',
             '<circle cx="12" cy="12" r="5"/>'],
    "point": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M10,16.5 V7.5 H13 A2.6,2.6 0 0 1 13,12.7 H10"/>'],
    "warning": ['<path d="M12,3.5 L21.5,20 H2.5 Z"/>',
                '<path d="M12,9.5 V14"/>',
                '<circle cx="12" cy="17" r="0.9" fill="CUR" stroke="none"/>'],
    "check": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M8,12.3 L11,15.3 L16.3,9.3"/>'],
    "clock": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M12,7 V12 L15.5,14"/>'],
    "lock": ['<rect x="5" y="10.5" width="14" height="10.5" rx="2"/>',
             '<path d="M8,10.5 V7.5 A4,4 0 0 1 16,7.5 V10.5"/>'],
    "key": ['<circle cx="7.5" cy="16" r="4.5"/>',
            '<path d="M10.7,12.8 L20,3.5 M16.5,7 L19,9.5 M14,9.5 L16,11.5"/>'],
    "document": ['<path d="M6,2.5 H14 L19,7.5 V21.5 H6 Z"/>',
                 '<path d="M14,2.5 V7.5 H19 M9,12.5 H16 M9,16.5 H16"/>'],
    "bell": ['<path d="M6,16 V11 A6,6 0 0 1 18,11 V16 L19.5,18 H4.5 Z"/>',
             '<path d="M10,21 H14"/>'],
    "flag": ['<path d="M5,21 V3.5"/>',
             '<path d="M5,4 H17.5 L15,8 L17.5,12 H5"/>'],
    "shield": ['<path d="M12,3 L20,6 V12 C20,16.5 16.5,20 12,21.5 C7.5,20 4,16.5 4,12 V6 Z"/>'],
    "search": ['<circle cx="10.5" cy="10.5" r="6.5"/>',
               '<path d="M15.5,15.5 L21,21"/>'],
    "funnel": ['<path d="M3,4 H21 L14,12.5 V19 L10,21 V12.5 Z"/>'],
    "queue": ['<rect x="3" y="4" width="18" height="4.5" rx="1.2"/>',
              '<rect x="3" y="10" width="18" height="4.5" rx="1.2"/>',
              '<rect x="3" y="16" width="18" height="4.5" rx="1.2"/>'],
    "workflow": ['<rect x="2.5" y="3" width="7" height="6" rx="1.5"/>',
                 '<rect x="14.5" y="9" width="7" height="6" rx="1.5"/>',
                 '<rect x="2.5" y="15" width="7" height="6" rx="1.5"/>',
                 '<path d="M9.5,6 H12 V12 H14.5 M12,12 V18 H9.5"/>'],
}


def text_width(s, size):
    """描画幅の見積もり（px）。Hiragino Sans の実測に合わせて半角は 0.62 倍で見る。"""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += size * 0.3
        elif unicodedata.east_asian_width(ch) in ("F", "W", "A"):
            w += size
        else:
            w += size * 0.62
    return w


class Slide:
    def __init__(self, title, description, width=960, height=540, margin=24, pad=20):
        self.W, self.H, self.M, self.PAD = width, height, margin, pad
        self.out = []
        self.warnings = []
        a = self.out.append
        a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
          f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img" aria-label="{escape(description)}">')
        a(f"<title>{escape(title)}</title>")
        a('<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
          '<feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0F172A" flood-opacity="0.07"/></filter></defs>')
        a(f'<rect width="{width}" height="{height}" fill="{C.BG}"/>')

    # ---- 基本要素 ----
    def raw(self, svg):
        self.out.append(svg)

    def text(self, x, y, s, size=13, color=C.TEXT, weight=400, anchor="start", max_width=None):
        """max_width を渡すと、見積もり幅が超えたときに警告を出す。"""
        if max_width is not None:
            w = text_width(s, size)
            if w > max_width:
                self.warnings.append(f"はみ出しの疑い: 「{s}」 見積もり {w:.0f}px > 許容 {max_width:.0f}px")
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
                        f'fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')

    def card(self, x, y, w, h, border=C.LINE, fill=C.CARD):
        """角丸 12px・影付きのカード。影が描画されない環境でも枠線で区切りが分かる。"""
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="12" fill="{fill}" '
                        f'stroke="{border}" stroke-width="1" filter="url(#sh)"/>')

    def line(self, x1, y1, x2, y2, color=C.LINE, width=1):
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"/>')

    def arrow(self, x1, x2, y):
        """右向きの矢印。marker を使わず、線と先端を 1 本の path で描く。"""
        self.out.append(f'<path d="M{x1:.1f},{y:.1f} H{x2:.1f} M{x2-6:.1f},{y-6:.1f} L{x2:.1f},{y:.1f} L{x2-6:.1f},{y+6:.1f}" '
                        f'stroke="{C.ARROW}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')

    def arrow_down(self, x, y1, y2):
        self.out.append(f'<path d="M{x:.1f},{y1:.1f} V{y2:.1f} M{x-6:.1f},{y2-6:.1f} L{x:.1f},{y2:.1f} L{x+6:.1f},{y2-6:.1f}" '
                        f'stroke="{C.ARROW}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')

    def pill(self, x, y, label, fill=C.PRIMARY, color="#FFFFFF", border=None, h=22, size=12, w=None):
        """番号・分類のバッジ。w を省くと文字幅から決める。戻り値はバッジの幅。"""
        if w is None:
            w = round(text_width(label, size) + 24)
        s = f' stroke="{border}" stroke-width="1"' if border else ""
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}"{s}/>')
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, color, 600, "middle")
        return w

    def dot(self, x, y, color, r=3.5):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')

    def numbered(self, cx, cy, n, r=12, fill=C.PRIMARY):
        self.out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>')
        self.text(cx, cy + 5, str(n), 13, "#FFFFFF", 600, "middle")

    def icon(self, name, x, y, size=22, color=C.SUB):
        """アイコン（ICONS のキー）。(x, y) は左上。線の太さは大きさによらず 1.75px に見える。"""
        k = size / 24
        body = "".join(ICONS[name]).replace("CUR", color)
        self.out.append(f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="none" stroke="{color}" '
                        f'stroke-width="{1.75 / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')

    def connector(self, x1, y1, x2, y2, color=C.ARROW, label=None):
        """任意の向きの矢印（終点に先端）。label を渡すと線の中点の上に小さく書く。"""
        import math
        if math.hypot(x2 - x1, y2 - y1) < 28:
            self.warnings.append(f"矢印が短い: ({x1:.0f},{y1:.0f})→({x2:.0f},{y2:.0f}) は "
                                 f"{math.hypot(x2 - x1, y2 - y1):.0f}px。28px 以上にする")
        ang = math.atan2(y2 - y1, x2 - x1)
        hx1 = x2 - 7 * math.cos(ang - 0.6)
        hy1 = y2 - 7 * math.sin(ang - 0.6)
        hx2 = x2 - 7 * math.cos(ang + 0.6)
        hy2 = y2 - 7 * math.sin(ang + 0.6)
        self.out.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} M{hx1:.1f},{hy1:.1f} L{x2:.1f},{y2:.1f} L{hx2:.1f},{hy2:.1f}" '
                        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 - 8, label, 12, C.SUB, 400, "middle")

    def titled(self, x, y, icon, title, size=15, color=C.TEXT, icon_color=C.SUB, max_width=None):
        """アイコン付きの見出し。y は文字のベースライン。"""
        self.icon(icon, x, y - size + 1 - (22 - size) / 2, 22, icon_color)
        self.text(x + 30, y, title, size, color, 600, max_width=None if max_width is None else max_width - 30)

    # ---- 配置 ----
    def columns(self, n, gap=12, left=None, right=None):
        """左右の余白の内側を n 等分する。戻り値は (幅, 各列の x)。"""
        left = self.M if left is None else left
        right = self.W - self.M if right is None else right
        w = (right - left - gap * (n - 1)) / n
        return w, [left + i * (w + gap) for i in range(n)]

    # ---- 組み合わせ部品 ----
    def header(self, title, meta=None, y=42):
        """スライドの見出し（20px・600）と、右上の補足（12px）。見出しには結論を書く。"""
        self.text(self.M, y, title, 20, C.TEXT, 600, max_width=self.W - 2 * self.M - (220 if meta else 0))
        if meta:
            self.text(self.W - self.M, y, meta, 12, C.SUB, 400, "end")

    def section(self, y, title):
        """段の見出し（15px・600）。"""
        self.text(self.M, y, title, 15, C.TEXT, 600, max_width=self.W - 2 * self.M)

    def stat(self, x, y, w, label, value, color=C.TEXT, h=58, icon=None):
        """ラベルと数値の組。数値は 16px・500。icon を渡すと右上にアイコンを置く。"""
        self.card(x, y, w, h)
        room = w - 2 * self.PAD - (30 if icon else 0)
        self.text(x + self.PAD, y + 22, label, 12, C.SUB, max_width=room)
        self.text(x + self.PAD, y + 45, value, 16, color, 500, max_width=room)
        if icon:
            self.icon(icon, x + w - self.PAD - 22, y + (h - 22) / 2, 22, color if color != C.TEXT else C.SUB)

    def stats(self, y, items, gap=12):
        """stat を横一列に並べる。items = [(ラベル, 値, 色) または (ラベル, 値, 色, アイコン), ...]"""
        w, xs = self.columns(len(items), gap)
        for x, item in zip(xs, items):
            label, value, color = item[:3]
            self.stat(x, y, w, label, value, color, icon=item[3] if len(item) > 3 else None)

    def ratio(self, x, y, w, label, value, value_color, part_label, fraction,
              fill=C.GREEN, track=C.ORANGE_BG, h=58):
        """全体の値と、そのうちの割合を 1 本の帯で示すカード。
        左に全体の値、右に「うち〜」の説明と帯。帯の塗りが fraction（0〜1）。"""
        self.card(x, y, w, h)
        self.text(x + self.PAD, y + 22, label, 12, C.SUB)
        self.text(x + self.PAD, y + 45, value, 16, value_color, 500)
        left = x + self.PAD + max(text_width(value, 16), text_width(label, 12)) + 24
        right = x + w - self.PAD
        self.text(right, y + 22, part_label, 12, C.SUB, 400, "end", max_width=right - left)
        bw = right - left
        self.raw(f'<rect x="{left:.1f}" y="{y + 33:.1f}" width="{bw:.1f}" height="10" rx="5" fill="{track}"/>')
        self.raw(f'<rect x="{left:.1f}" y="{y + 33:.1f}" width="{bw * fraction:.1f}" height="10" rx="5" fill="{fill}"/>')

    def node(self, x, y, w, h, icon, title, sub=(), accent=None):
        """図解の要素（人・システム・データなど）。上にアイコン、下に名前と説明を中央そろえで書く。"""
        color = accent or C.TEXT
        self.card(x, y, w, h, accent or C.LINE)
        self.icon(icon, x + w / 2 - 12, y + 14, 24, accent or C.SUB)
        self.text(x + w / 2, y + 58, title, 13, color, 600, "middle", max_width=w - 16)
        for j, s_ in enumerate(sub):
            self.text(x + w / 2, y + 78 + j * 17, s_, 12, C.SUB, 400, "middle", max_width=w - 16)

    def zone(self, x, y, w, h, label):
        """持ち主や環境の区域を示す枠（淡い背景・破線）。label は左上に書く。中に node を置く。"""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="#F1F5F9" '
                 f'stroke="#CBD5E1" stroke-width="1" stroke-dasharray="4 4"/>')
        self.text(x + 14, y + 19, label, 12, C.SUB, 600, max_width=w - 28)

    def span(self, x1, x2, y, label, color=C.SUB):
        """x1〜x2 の範囲を示す線と、その上のラベル。「メールを送る前」などの区切りに使う。"""
        self.raw(f'<path d="M{x1:.1f},{y + 6:.1f} V{y:.1f} H{x2:.1f} V{y + 6:.1f}" stroke="{color}" stroke-width="1.5" '
                 f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        self.text((x1 + x2) / 2, y - 7, label, 12, color, 500, "middle", max_width=x2 - x1)

    def timeline(self, y, items, gap=16, left=None, right=None):
        """時刻順の出来事を等間隔に並べる（間隔は時間の長さに比例しない）。
        items = [(時刻, 見出し, [説明...], 強調色 or None), ...]。y は軸の位置。"""
        w, xs = self.columns(len(items), gap, left, right)
        x0 = xs[0]
        x1 = xs[-1] + w
        self.line(x0, y, x1, y, C.LINE, 2)
        for x, (t, title, desc, accent) in zip(xs, items):
            color = accent or C.TEXT
            self.dot(x + 6, y, accent or C.PRIMARY, 5)
            self.text(x, y - 14, t, 14, color, 600, max_width=w)
            self.text(x, y + 28, title, 13, color, 600, max_width=w)
            for j, d in enumerate(desc):
                self.text(x, y + 48 + j * 18, d, 12, C.SUB, max_width=w)
        return w, xs

    # ---- 分岐図 ----
    def box(self, x, y, w, h, title, sub=None, fill=C.CARD, border=C.LINE, color=C.TEXT, rx=10, size=13):
        """分岐図の処理（影なしの四角）。文字は中央そろえ。"""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                 f'stroke="{border}" stroke-width="1.2"/>')
        if sub:
            self.text(x + w / 2, y + h / 2 - 3, title, size, color, 600, "middle", max_width=w - 16)
            self.text(x + w / 2, y + h / 2 + 14, sub, 12, C.SUB, 400, "middle", max_width=w - 16)
        else:
            self.text(x + w / 2, y + h / 2 + size * 0.36, title, size, color, 600, "middle", max_width=w - 16)

    def decision(self, x, y, w, h, label):
        """分岐図の判断（「プランがあるか」など）。淡い青の角丸で、処理の四角と見分ける。"""
        self.box(x, y, w, h, label, fill=C.PRIMARY_BG, border=C.PRIMARY, color=C.PRIMARY, rx=h / 2)

    def terminal(self, x, y, w, h, label, color=C.SUB, sub=None):
        """分岐図の終わり（ACK・NACK・終端など）。color で結果の意味を示す。"""
        bg = {C.GREEN: C.GREEN_BG, C.ORANGE: C.ORANGE_BG, C.PRIMARY: C.PRIMARY_BG}.get(color, "#F1F5F9")
        self.box(x, y, w, h, label, sub=sub, fill=bg, border=color, color=color if color != C.SUB else C.TEXT,
                 rx=min(h / 2, 14))

    def elbow(self, pts, color=C.ARROW, width=2):
        """折れ線の矢印（終点に先端）。pts = [(x, y), ...]。縦横だけで曲げると読みやすい。
        最後の区間が 28px 未満だと先端がつぶれて見えるので警告する。ラベルは線の上に重ねず、横に置く。"""
        import math
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        if math.hypot(bx - ax, by - ay) < 28:
            self.warnings.append(f"矢印が短い: ({ax:.0f},{ay:.0f})→({bx:.0f},{by:.0f}) は "
                                 f"{math.hypot(bx - ax, by - ay):.0f}px。28px 以上にする")
        ang = math.atan2(by - ay, bx - ax)
        h1 = (bx - 7 * math.cos(ang - 0.6), by - 7 * math.sin(ang - 0.6))
        h2 = (bx - 7 * math.cos(ang + 0.6), by - 7 * math.sin(ang + 0.6))
        d += f" M{h1[0]:.1f},{h1[1]:.1f} L{bx:.1f},{by:.1f} L{h2[0]:.1f},{h2[1]:.1f}"
        self.raw(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')

    def edge_label(self, x, y, label, color=C.SUB, bg=C.BG):
        """矢印に添えるラベル（「はい」「いいえ」など）。背景を塗って線と重ならないようにする。y は中心。"""
        w = text_width(label, 12) + 10
        self.raw(f'<rect x="{x - w / 2:.1f}" y="{y - 9:.1f}" width="{w:.1f}" height="18" rx="4" fill="{bg}"/>')
        self.text(x, y + 4.3, label, 12, color, 500, "middle")

    # ---- 模式図・軸・範囲 ----
    def sketch(self, x, y, w, h, xlabels=(), ylabel=None, note="模式図（実際の値ではない）"):
        """形を説明するための模式図の枠。戻り値の Sketch に 0〜1 の座標で線や面を描く。
        実データのグラフではないので、note を必ず表示する。"""
        self.line(x, y, x, y + h, C.ARROW, 1.2)
        self.line(x, y + h, x + w, y + h, C.ARROW, 1.2)
        if ylabel:
            self.text(x + 6, y + 4, ylabel, 12, C.SUB)
        if note:
            self.text(x + w, y - 8, note, 12, C.SUB, 400, "end")
        n = len(xlabels)
        for i, lb in enumerate(xlabels):
            if not lb:
                continue
            fx = 0 if n == 1 else i / (n - 1)
            anchor = "start" if i == 0 else ("end" if i == n - 1 else "middle")
            self.text(x + fx * w, y + h + 18, lb, 12, C.SUB, 400, anchor)
        return Sketch(self, x, y, w, h)

    def scale(self, x, w, v0, v1):
        """値 v0〜v1 を x〜x+w に写す関数を返す（時間に比例した軸などに使う）。"""
        return lambda v: x + (v - v0) / (v1 - v0) * w

    def band(self, x1, x2, y, h, color, label=None, label_color=None):
        """時間帯や範囲を示す帯。color は帯の色。label は帯の右に書く。"""
        bg = {C.GREEN: C.GREEN_BG, C.ORANGE: C.ORANGE_BG, C.PRIMARY: C.PRIMARY_BG}.get(color, "#F1F5F9")
        self.raw(f'<rect x="{x1:.1f}" y="{y:.1f}" width="{max(x2 - x1, 4):.1f}" height="{h}" rx="{min(h / 2, 5)}" '
                 f'fill="{bg}" stroke="{color}" stroke-width="1.2"/>')
        if label:
            self.text(x2 + 8, y + h / 2 + 4.3, label, 12, label_color or C.SUB, 500)

    def range_bar(self, x, y, w, label, lo, hi, vmax, value, color=C.PRIMARY, label_w=150, value_w=96):
        """最小〜最大の範囲を示す横棒。y は行の中心。数値を正確に比べるグラフは、グラフ用のライブラリで作る。"""
        self.text(x, y + 4.5, label, 12.5, C.TEXT, 400, max_width=label_w - 8)
        tx, tw = x + label_w, w - label_w - value_w
        self.raw(f'<rect x="{tx:.1f}" y="{y - 4:.1f}" width="{tw:.1f}" height="8" rx="4" fill="{C.LINE}"/>')
        x1, x2 = tx + lo / vmax * tw, tx + hi / vmax * tw
        self.raw(f'<rect x="{x1:.1f}" y="{y - 4:.1f}" width="{max(x2 - x1, 6):.1f}" height="8" rx="4" fill="{color}"/>')
        self.text(x + w, y + 4.5, value, 12.5, color if color != C.PRIMARY else C.TEXT, 500, "end")

    def chain(self, y, items, h=104, gap=44):
        """node を横一列に並べ、矢印でつなぐ。items = [(アイコン, 名前, [説明...], 強調色 or None), ...]"""
        w, xs = self.columns(len(items), gap)
        for i, (x, (icon, title, sub, accent)) in enumerate(zip(xs, items)):
            self.node(x, y, w, h, icon, title, sub, accent)
            if i < len(items) - 1:
                self.connector(x + w + 6, y + h / 2, x + w + gap - 6, y + h / 2)
        return w, xs

    def flow(self, y, items, h=84, gap=28, pad=16):
        """矢印でつないだ横並びのボックス。
        items = [(見出し, [説明 1 行目, 2 行目], 強調色 or None), ...]
        強調色を渡したボックスは、枠と見出しをその色にする。"""
        w, xs = self.columns(len(items), gap)
        for i, (x, (title, desc, accent)) in enumerate(zip(xs, items)):
            self.card(x, y, w, h, accent or C.LINE)
            self.text(x + pad, y + 28, title, 14, accent or C.TEXT, 600, max_width=w - 2 * pad)
            for j, d in enumerate(desc):
                self.text(x + pad, y + 51 + j * 18, d, 12, C.SUB, max_width=w - 2 * pad)
            if i < len(items) - 1:
                self.arrow(x + w + gap / 2 - 7, x + w + gap / 2 + 7, y + h / 2)
        return w, xs

    def bullets(self, x, y, w, items, size=13, step=24):
        """点付きの箇条書き。y は 1 行目のベースライン。"""
        for j, item in enumerate(items):
            yy = y + j * step
            self.dot(x + 3, yy - size * 0.35, C.ARROW, 2.5)
            self.text(x + 12, yy, item, size, C.TEXT, max_width=w - 12)

    def status(self, x, y, label, color):
        """丸印と状態のラベル（完了はグリーン、未着手はグレー、対応中はオレンジ）。"""
        self.dot(x + 4, y - 4, color)
        self.text(x + 14, y, label, 12, color, 500)

    def table(self, x, y, w, headers, col_x, rows, highlight=(), head_h=30, row_h=31):
        """表。col_x は各列の左端（表の左端からの距離）。
        セルは文字列か (文字列, 色, 太さ)。highlight は背景を淡い青にする行の番号。"""
        n = len(rows)
        self.card(x, y, w, head_h + row_h * n)
        bounds = list(col_x) + [w]
        for k, hd in enumerate(headers):
            self.text(x + col_x[k], y + 20, hd, 12, C.SUB, 500)
        for i, row in enumerate(rows):
            ry = y + head_h + i * row_h
            if i in highlight:
                bottom = 11 if i == n - 1 else 0
                self.raw(f'<rect x="{x + 1:.1f}" y="{ry:.1f}" width="{w - 2:.1f}" height="{row_h - bottom}" fill="{C.PRIMARY_BG}"/>')
            self.line(x, ry, x + w, ry)
            for k, cell in enumerate(row):
                s, color, weight = (cell, C.TEXT, 400) if isinstance(cell, str) else cell
                self.text(x + col_x[k], ry + row_h / 2 + 5, s, 12.5 if k else 13, color, weight,
                          max_width=bounds[k + 1] - col_x[k] - 12)

    def steps(self, x, y, items, step=50):
        """縦に並ぶ番号付きの手順。items = [(見出し, 説明), ...]。y は 1 つ目の丸の中心。"""
        for i, (title, desc) in enumerate(items):
            cy = y + i * step
            self.numbered(x + 12, cy, i + 1)
            self.text(x + 34, cy - 1, title, 14, C.TEXT, 600)
            self.text(x + 34, cy + 18, desc, 12, C.SUB)
            if i < len(items) - 1:
                self.line(x + 12, cy + 16, x + 12, cy + step - 16, C.LINE, 2)

    # ---- 出力 ----
    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.out + ["</svg>"]) + "\n")
        for w in self.warnings:
            print("WARN", w, file=sys.stderr)
        return path

    def render(self, png_path, svg_path=None, scale=2):
        svg_path = svg_path or os.path.splitext(png_path)[0] + ".svg"
        if not os.path.exists(svg_path):
            self.save(svg_path)
        return render(svg_path, png_path, scale)


class Sketch:
    """Slide.sketch() が返す模式図。座標は左下が (0, 0)、右上が (1, 1)。"""

    def __init__(self, slide, x, y, w, h):
        self.s, self.x, self.y, self.w, self.h = slide, x, y, w, h

    def p(self, fx, fy):
        return self.x + fx * self.w, self.y + (1 - fy) * self.h

    def line(self, pts, color=C.PRIMARY, width=2.5, dash=False):
        d = "M" + " L".join("{:.1f},{:.1f}".format(*self.p(fx, fy)) for fx, fy in pts)
        da = ' stroke-dasharray="6 5"' if dash else ""
        self.s.raw(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
                   f'stroke-linecap="round" stroke-linejoin="round"{da}/>')

    def area(self, pts, color, opacity=0.18):
        d = "M" + " L".join("{:.1f},{:.1f}".format(*self.p(fx, fy)) for fx, fy in pts) + " Z"
        self.s.raw(f'<path d="{d}" fill="{color}" fill-opacity="{opacity}" stroke="none"/>')

    def label(self, fx, fy, text, color=C.SUB, anchor="start", size=12, weight=500):
        px, py = self.p(fx, fy)
        self.s.text(px, py, text, size, color, weight, anchor)


def render(svg_path, png_path, scale=2):
    """Chrome 系のブラウザのヘッドレスモードで PNG にする。サイズは SVG の width/height から読む。"""
    head = open(svg_path, encoding="utf-8").read(2000)
    w = int(float(re.search(r'width="([\d.]+)"', head).group(1)))
    h = int(float(re.search(r'height="([\d.]+)"', head).group(1)))
    svg_abs, png_abs = os.path.abspath(svg_path), os.path.abspath(png_path)
    if os.path.exists(png_abs):
        os.remove(png_abs)
    subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
                    f"--screenshot={png_abs}", pathlib.Path(svg_abs).as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png_abs


def catalog(png_path):
    """全アイコンの一覧を PNG にする。アイコンを足したり直したりしたら、これで形を確かめる。"""
    names = list(ICONS)
    cols = 7
    rows = (len(names) + cols - 1) // cols
    s = Slide("アイコン一覧", "svgparts のアイコン一覧", width=cols * 120 + 48, height=rows * 96 + 48)
    for i, name in enumerate(names):
        x = 24 + (i % cols) * 120
        y = 24 + (i // cols) * 96
        s.card(x + 4, y + 4, 112, 88)
        s.icon(name, x + 60 - 16, y + 18, 32, C.TEXT)
        s.text(x + 60, y + 76, name, 12, C.SUB, 400, "middle")
    svg = os.path.splitext(png_path)[0] + ".svg"
    s.save(svg)
    return render(svg, png_path)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "render":
        print(render(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "icons":
        print(catalog(sys.argv[2]))
    else:
        print("usage: svgparts.py render in.svg out.png | svgparts.py icons out.png", file=sys.stderr)
        sys.exit(2)
