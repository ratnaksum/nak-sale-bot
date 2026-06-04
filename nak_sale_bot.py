import re
import logging
from datetime import date
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
BOT_TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

orders = defaultdict(lambda: defaultdict(list))

def today_key():
    return date.today().isoformat()

ORDER_PATTERN = re.compile(
    r"(?P<name>\S+)\s+(?P<code>[A-Za-z0-9\-]+)\s+[xX×\*](?P<qty>\d+)",
    re.MULTILINE,
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    matches = ORDER_PATTERN.findall(text)
    if not matches:
        return
    day = today_key()
    added = []
    for name, code, qty in matches:
        code = code.upper()
        qty = int(qty)
        orders[day][code].append({"name": name, "qty": qty})
        added.append(f"✅ {name} → {code} x{qty}")
    if added:
        await update.message.reply_text("\n".join(added), quote=True)

async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    day = today_key()
    if not args:
        await update.message.reply_text("📌 วิธีใช้: /สรุป H1418\nหรือ /สรุปทั้งหมด")
        return
    code = args[0].upper()
    entries = orders[day].get(code, [])
    if not entries:
        await update.message.reply_text(f"ไม่พบออเดอร์ {code} วันนี้ ({day})")
        return
    lines = [f"📦 สรุปยอด *{code}* วันที่ {day}\n"]
    total = 0
    for i, e in enumerate(entries, 1):
        lines.append(f"{i}. {e['name']}  x{e['qty']}")
        total += e["qty"]
    lines.append(f"\n🔢 รวมทั้งหมด: *{total} ชิ้น* จาก {len(entries)} ออเดอร์")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_summary_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = today_key()
    day_orders = orders.get(day, {})
    if not day_orders:
        await update.message.reply_text(f"ยังไม่มีออเดอร์วันนี้ ({day})")
        return
    lines = [f"📋 สรุปยอดทุกสินค้า วันที่ {day}\n"]
    grand_total = 0
    for code, entries in sorted(day_orders.items()):
        total = sum(e["qty"] for e in entries)
        names = ", ".join(e["name"] for e in entries)
        lines.append(f"*{code}*: {total} ชิ้น ({len(entries)} ออเดอร์)")
        lines.append(f"   └ {names}")
        grand_total += total
    lines.append(f"\n🛒 รวมทุกรายการ: *{grand_total} ชิ้น*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *NakSaleBot วิธีใช้*\n\n"
        "*บันทึกออเดอร์:*\n"
        "  `สมใจ H1418 x2`\n\n"
        "*สรุปยอด:*\n"
        "  `/สรุป H1418`\n"
        "  `/สรุปทั้งหมด`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("สรุปทั้งหมด", cmd_summary_all))
    app.add_handler(CommandHandler("สรุป", cmd_summary))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ NakSaleBot เริ่มทำงานแล้ว...")
    app.run_polling()

if __name__ == "__main__":
    main()
