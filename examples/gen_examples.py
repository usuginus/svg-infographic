"""README に載せる作例を描く。内容はすべて架空の例。

    python3 examples/gen_examples.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "svg-infographic", "skills", "svg-infographic", "scripts"))
from svgparts import Slide, C  # noqa: E402


def done(s, name):
    s.save(os.path.join(HERE, f"{name}.svg"))
    print(s.render(os.path.join(HERE, f"{name}.png")))


# ---- 1. 業務フロー ----
s = Slide("図書館の本の予約の流れ", "利用者が本を予約してから受け取るまでの流れと、システムが関わる手順")
s.header("予約は 4 段階。貸出中の本は、返却の時点で次の人に割り当てる", "業務フロー")
s.section(96, "予約から受け取りまで")
s.chain(116, [
    ("user", "利用者", ["Web で本を検索し", "予約を申し込む"], None),
    ("server", "予約システム", ["在庫を確かめ", "予約の順番を決める"], C.PRIMARY),
    ("bell", "通知", ["本が用意できたら", "メールで知らせる"], None),
    ("building", "図書館の窓口", ["7 日以内に", "受け取ってもらう"], C.GREEN),
], h=112)
s.section(282, "貸出中の本を予約したとき")
s.steps(s.M, 318, [
    ("予約の順番に並ぶ", "同じ本を予約した人の中で、申し込んだ順に並ぶ"),
    ("返却されたら割り当てる", "返却の処理と同時に、先頭の人に本を割り当てる"),
    ("期限内に受け取らなければ次の人へ", "受け取りの期限は 7 日。過ぎたら次の人に割り当て直す"),
], step=56)
s.zone(560, 300, 376, 150, "利用者から見えること")
s.bullets(580, 348, 336, [
    "予約の状態は「順番待ち」「用意できた」の 2 つ",
    "順番待ちの間は、何番目かを表示する",
    "用意できたらメールと Web の両方で知らせる",
], step=34)
done(s, "example-1-flow")


# ---- 2. 比較表 ----
s = Slide("通知の送り方の比較", "メール・プッシュ通知・SMS を、届く速さ・費用・向いている用途で比べる")
s.header("期限が近い連絡はプッシュ通知、記録に残す連絡はメールで送る", "方式の比較")
s.section(96, "3 つの方式の違い")
s.table(s.M, 112, s.W - 2 * s.M, ["方式", "届く速さ", "費用", "記録に残るか", "向いている用途"],
        [16, 150, 290, 420, 580], [
    ("メール", "数秒〜数分", "ほぼ無料", ("残る", C.GREEN, 500), "受付の控え・領収書"),
    ("プッシュ通知", ("数秒", C.GREEN, 500), "ほぼ無料", "残りにくい", "期限が近い連絡"),
    ("SMS", ("数秒", C.GREEN, 500), ("1 通ごとに費用", C.ORANGE, 500), "端末に残る", "本人確認の番号"),
], highlight=(1,), row_h=44)
s.section(330, "選び方")
for i, (q, qsub, a, asub, color) in enumerate([
    ("当日中に読んでほしい連絡か", "締め切りや受け取りの期限が近い", "プッシュ通知で送る", "アプリを入れていない人にはメールでも送る", C.PRIMARY),
    ("後で見返す必要がある連絡か", "受付の控え・領収書・規約の変更", "メールで送る", "件名に用件と日付を入れる", C.GREEN),
]):
    y = 350 + i * 82
    s.card(s.M, y, 380, 64)
    s.text(s.M + 20, y + 27, q, 14, C.TEXT, 600)
    s.text(s.M + 20, y + 48, qsub, 12, C.SUB)
    s.connector(s.M + 392, y + 32, 516, y + 32, label="はい")
    s.card(524, y, s.W - s.M - 524, 64, color)
    s.text(544, y + 27, a, 14, color, 600)
    s.text(544, y + 48, asub, 12, C.SUB)
done(s, "example-2-compare")


# ---- 3. 障害の振り返り ----
s = Slide("予約システムの障害の振り返り", "月曜の朝に予約システムの検索が止まった障害の経緯と再発防止策")
s.header("原因：月曜の朝に予約が集中し、検索サーバーの CPU が上限に達した", "障害の振り返り")
s.stats(64, [("止まった時間", "約 15 分", C.ORANGE, "clock"),
             ("影響した予約", "120 件", C.TEXT, "document"),
             ("再発防止策", "3 件（2 件完了）", C.TEXT, "check")])
s.section(164, "経緯")
s.timeline(222, [
    ("9:00", "開館と同時に予約が集中", ["検索の応答が", "遅くなり始める"], None),
    ("9:05", "検索が止まる", ["CPU が上限に達し", "応答を返せなくなる"], C.ORANGE),
    ("9:12", "サーバーを追加", ["検索サーバーを", "2 台から 4 台にする"], C.PRIMARY),
    ("9:20", "復旧", ["検索が通常の", "速さに戻る"], C.GREEN),
])
s.section(340, "再発防止策")
y = 358
for label, desc, st, color in [
    ("開館前にサーバーを増やす", "月曜と祝日明けは 8:30 に 4 台にしておく", "完了", C.GREEN),
    ("CPU の使用率で警告を出す", "80% を 5 分超えたら担当者に知らせる", "完了", C.GREEN),
    ("検索結果を一時保存する", "同じ検索は保存した結果を返し、負荷を減らす", "対応中", C.ORANGE),
]:
    s.card(s.M, y, s.W - 2 * s.M, 46)
    s.text(s.M + 20, y + 28, label, 14, C.TEXT, 600)
    s.text(s.M + 300, y + 28, desc, 12.5, C.SUB, max_width=500)
    s.status(s.W - s.M - 90, y + 28, st, color)
    y += 52
done(s, "example-3-incident")
