
    await update.message.reply_text("✅ Görev başarıyla eklendi.")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return

    with database() as db:
        rows = db.execute("""
            SELECT c.user_id,c.task_id,t.title
            FROM claims c
            JOIN tasks t ON t.id=c.task_id
            WHERE c.status='pending'
        """).fetchall()

    if not rows:
        await update.message.reply_text("Bekleyen görev yok.")
        return

    for uid, tid, title in rows:
        await update.message.reply_text(
            f"Kullanıcı: {uid}\nGörev: {title}\n"
            f"Onaylamak için: /approve {uid} {tid}"
        )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/approve USER_ID TASK_ID"
        )
        return

    try:
        uid, tid = map(int, context.args)
    except ValueError:
        await update.message.reply_text("Geçersiz ID.")
        return

    with database() as db:
        row = db.execute("""
            SELECT t.reward FROM claims c
            JOIN tasks t ON t.id=c.task_id
            WHERE c.user_id=? AND c.task_id=?
            AND c.status='pending'
        """, (uid, tid)).fetchone()

        if not row:
            await update.message.reply_text(
                "Bekleyen başvuru bulunamadı."
            )
            return

        db.execute("""
            UPDATE claims SET status='approved'
            WHERE user_id=? AND task_id=?
        """, (uid, tid))

        db.execute(
            "UPDATE users SET points=points+? WHERE id=?",
            (row[0], uid)
        )

    await update.message.reply_text("✅ Görev onaylandı.")

    try:
        await context.bot.send_message(
            uid, f"🎉 Görevin onaylandı! +{row[0]} NX"
        )
    except Exception:
        pass


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return

    with database() as db:
        users = db.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        points = db.execute(
            "SELECT COALESCE(SUM(points),0) FROM users"
        ).fetchone()[0]

        tasks = db.execute(
            "SELECT COUNT(*) FROM tasks WHERE active=1"
        ).fetchone()[0]

    await update.message.reply_text(
        f"◆ NOXEN ADMIN ◆\n\n"
        f"Users: {users}\n"
        f"Points: {points}\n"
        f"Active tasks: {tasks}"
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN eksik!")

    setup()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(CallbackQueryHandler(buttons))

    print("NOXEN SYSTEM ONLINE")

    app.run_polling()


if __name__ == "__main__":
    main()
