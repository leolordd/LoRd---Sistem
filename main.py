import asyncio
from fastapi import FastAPI, Form, responses
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, Text, KeyboardButtonColor
import uvicorn

# ⚠️ НАСТРОЙКИ (Вставь свои данные)
VK_TOKEN = "ТВОЙ_ТОКЕН_ГРУППЫ_ВК"
ADMIN_CHAT_ID = 2000000001  # peer_id вашей админ-конфы, куда будут лететь заявки

# Инициализация сайта и бота
app = FastAPI()
bot = Bot(token=VK_TOKEN)

# Временная база данных в оперативной памяти (для теста)
applications = {}

# --- ВЕБ-САЙТ (FastAPI) ---

@app.get("/")
async def save_index():
    # Отдаем файл анкеты index.html
    return responses.FileResponse("index.html")

@app.post("/submit")
async def handle_submit(nickname: str = Form(...), vk_link: str = Form(...), rank: str = Form(...), stats_link: str = Form(...)):
    app_id = len(applications) + 1
    applications[app_id] = {"nick": nickname, "vk": vk_link, "rank": rank, "stats": stats_link, "status": "Ожидание"}
    
    # Формируем клавиатуру для админов с кнопками
    keyboard = (
        Keyboard(inline=True)
        .add(Text(f"✅ Одобрить {app_id}", {"cmd": f"accept_{app_id}"}), color=KeyboardButtonColor.POSITIVE)
        .add(Text(f"❌ Отказать {app_id}", {"cmd": f"reject_{app_id}"}), color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    # Текст заявки в админ-конфу
    report_text = (
        "📊 **Поступила новая заявка!**\n\n"
        f"👤 Ник: {nickname}\n"
        f"🔗 ВК: {vk_link}\n"
        f"💼 Должность: {rank}\n"
        f"📸 Статистика: {stats_link}"
    )
    
    # Отправляем ботом заявку админам
    try:
        await bot.api.messages.send(peer_id=ADMIN_CHAT_ID, message=report_text, keyboard=keyboard, random_id=0)
    except Exception as e:
        print(f"Ошибка отправки в ВК: {e}")

    return responses.HTMLResponse("<h2>✅ Ваша анкета успешно отправлена! Ожидайте вердикта в ЛС.</h2>")


# --- БОТ ВК (Обработка кнопок одобрения) ---

@bot.on.chat_message()
async def handle_buttons(message: Message):
    if message.payload:
        import json
        payload = json.loads(message.payload)
        cmd = payload.get("cmd", "")
        
        if cmd.startswith("accept_"):
            app_id = int(cmd.split("_")[1])
            if app_id in applications:
                user_data = applications[app_id]
                await message.answer(f"🟢 Заявка #{app_id} ({user_data['nick']}) успешно ОДОБРЕНА!")
                # Здесь в будущем добавим отправку сообщения самому игроку в ЛС со ссылкой на конфу
                
        elif cmd.startswith("reject_"):
            app_id = int(cmd.split("_")[1])
            if app_id in applications:
                user_data = applications[app_id]
                await message.answer(f"🔴 Заявка #{app_id} ({user_data['nick']})ОТКЛОНЕНА.")

# Асинхронный запуск сайта и бота одновременно
async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    
    # Запускаем сайт и бота параллельно
    await asyncio.gather(
        server.serve(),
        bot.run_forever()
    )

if __name__ == "__main__":
    asyncio.run(main())
  
