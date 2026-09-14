import os, asyncio
import yt_dlp
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CODE YAHI DALNA HAI (ENV se bhi lega) ---
API_ID = int(os.getenv("37146575"))
API_HASH = os.getenv("4617e8b7d1040d7d895ec39de8eae4e5")
BOT_TOKEN = os.getenv("8252566284:AAH84AVugAXHYgvrJvPqI7-6QfC3GCwLYZ8")
SESSION_STRING = os.getenv("BQI2z88ASotzhCfCbI024XcDPNqOuzV7a7mkxUeqEPOhV_-J1zQMsCFem1M2DlT5rdvDi5E-GyXmvlL8jiKqvZPyLKTqIbceF7PXctsaW4T6zSnwIhPML5-q9x8x_E5u6uH8JfhJIPWpH0J29QzQt1gxn3oVvatVcwjh0lveIFwjkMu2hoFC0LGwoSEF6Jyw7k8OLQhBSGciwSBesvCvze0aw6Ls_-3XErM1GbQlJtkShPavbG_gN_MQ3Fo00VGLfI9qWyGetrH6TpbtXL3Z_PsYaSj1yBkA6pbKrBZcCu28UZNRdcaQqG0PDDVYqQCp_GDo87Va5SOqLGqfK8WvxTIQXcBnZgAAAAH3BaEwAA")
# ---------------------------------------------

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_app)

queues = {}
WATERMARK = "\n\n@epic_india"

def get_url(query):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True, 'default_search': 'ytsearch1'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info['title']

@call_py.on_update()
async def stream_end_handler(_, update):
    # BUG FIX: sahi se check karega stream end hua ya nahi
    if hasattr(update, 'stream_end') and update.stream_end:
        chat_id = update.chat_id
        if chat_id in queues and queues[chat_id]:
            queues[chat_id].pop(0)
            if queues[chat_id]:
                next_data = queues[chat_id][0]
                url, title = await asyncio.to_thread(get_url, next_data['query'])
                await call_py.play(chat_id, MediaStream(url))
                await app.send_message(chat_id, f"▶️ **Now Playing:** {title}\n👤 Requested by: {next_data['mention']}{WATERMARK}")
            else:
                queues.pop(chat_id, None)

@app.on_message(filters.command(["play","vplay","stop","skip","queue","pause","resume"]) & filters.group)
async def handler(_, m):
    mention = m.from_user.mention if m.from_user else "Unknown"
    cmd = m.command[0].lower()

    if cmd == "stop":
        queues.pop(m.chat.id, None)
        try: await call_py.leave(m.chat.id)
        except: pass
        await m.reply(f"⏹ **Stopped & Queue cleared**\nBy: {mention}{WATERMARK}")
        return

    if cmd == "skip":
        if m.chat.id in queues and queues[m.chat.id]:
            old = queues[m.chat.id][0]
            queues[m.chat.id].pop(0)
            if queues[m.chat.id]:
                nxt = queues[m.chat.id][0]
                url, _ = await asyncio.to_thread(get_url, nxt['query'])
                await call_py.play(m.chat.id, MediaStream(url))
                await m.reply(f"⏭ **Skipped:** {old['title']}\n▶️ **Now:** {nxt['title']}\n👤 Requested by: {nxt['mention']}{WATERMARK}")
            else:
                try: await call_py.leave(m.chat.id)
                except: pass
                await m.reply(f"⏭ Skipped, Queue empty{WATERMARK}")
        else:
            await m.reply(f"Kuch baj hi nahi raha skip karne ko{WATERMARK}")
        return

    if cmd == "queue":
        q = queues.get(m.chat.id, [])
        if not q:
            await m.reply(f"Queue khali hai{WATERMARK}")
            return
        text = "**🎵 Queue:**\n"
        for i, d in enumerate(q, 1):
            text += f"{i}. {d['title']} - {d['mention']}\n"
        await m.reply(text + WATERMARK)
        return

    if len(m.command) < 2:
        await m.reply(f"Gaane ka naam to de! Ex: `/play kesariya`{WATERMARK}")
        return

    query = m.text.split(None, 1)[1]
    status = await m.reply(f"🔎 **Searching:** `{query}`\n👤 By: {mention}{WATERMARK}")

    try:
        url, title = await asyncio.to_thread(get_url, query)
    except Exception as e:
        await status.edit(f"❌ Search failed: {e}{WATERMARK}")
        return

    data = {"query": query, "title": title, "mention": mention}

    if m.chat.id not in queues: queues[m.chat.id] = []

    if not queues[m.chat.id]:
        queues[m.chat.id].append(data)
        try:
            await call_py.play(m.chat.id, MediaStream(url))
            await status.edit(f"▶️ **Now Playing:** {title}\n👤 **Requested by:** {mention}\n📢 **GC me update aa gaya**{WATERMARK}")
        except Exception as e:
            queues[m.chat.id].pop(0)
            await status.edit(f"❌ Play Error: {e}{WATERMARK}")
    else:
        queues[m.chat.id].append(data)
        await status.edit(f"➕ **Added to Queue #{len(queues[m.chat.id])}**\n🎵 {title}\n👤 **Requested by:** {mention}{WATERMARK}")

# Private me bot ka intro
@app.on_message(filters.command(["start","help"]) & filters.private)
async def start_private(_, m):
    await m.reply(f"Hi {m.from_user.mention}!\nMain Music Bot hu, mujhe kisi bhi GC me add karke /play kar sakte ho.\n\n**Commands:** /play /skip /stop /queue{WATERMARK}")

async def main():
    await user_app.start()
    await app.start()
    await call_py.start()
    print("BOT LIVE - All GC + MediaStream + @epic_india")
    await asyncio.Event().wait()

asyncio.run(main())
