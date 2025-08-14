from bot import cmd1
from datetime import datetime as dt
import os
from bot import (
    APP_ID,
    API_HASH,
    DOWNLOAD_LOCATION,
    TG_BOT_TOKEN,
    BOT_USERNAME,
    SESSION_NAME,
    
    data,
    app,
    crf,
    watermark,
    resolution,
    bit,
    preset
)
from bot.helper_funcs.utils import add_task, on_task_complete
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.enums import ParseMode

from bot.plugins.incoming_message_fn import (
    incoming_start_message_f,
    incoming_compress_message_f,
    incoming_cancel_message_f
)

from bot.plugins.status_message_fn import (
    exec_message_f,
    upload_log_file
)

from bot.commands import Command
from bot.plugins.call_back_button_handler import button

uptime = dt.now()

def ts(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
        + ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]

# Add eval_message_f function
async def eval_message_f(app, message):
    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
        result = eval(cmd)
        await message.reply_text(f"Result: {result}")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    # create download directory, if not exist
    if not os.path.isdir(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)
    
    # START command
    incoming_start_message_handler = MessageHandler(
        incoming_start_message_f,
        filters=filters.command(["start", f"start@{BOT_USERNAME}"])
    )
    app.add_handler(incoming_start_message_handler)
    
    @app.on_message(filters.incoming & filters.command(["compress", f"compress@{BOT_USERNAME}"]))
    async def compress_command(app, message):
        query = await message.reply_text("Added to Queue ⏰...\nPlease be patient, Compress will start soon", quote=True)
        data.append(message.reply_to_message)
        if len(data) == 1:
            await query.delete()   
            await add_task(message.reply_to_message)     
            
    @app.on_message(filters.incoming & filters.command(["480p", f"480p@{BOT_USERNAME}"]))
    async def set_480p(app, message):
        await message.reply_text("480p Mode has been set", quote=True)
        cmd1.insert(0, "-pix_fmt yuv420p -preset medium -s 854x480 -crf 28 -profile:a  aac_he_v2 -c:a libopus -ac 1 -vbr 2 -ab 60k -c:s copy -y")
                 
    @app.on_message(filters.incoming & filters.command(["1080p", f"1080p@{BOT_USERNAME}"]))
    async def set_1080p(app, message):
        await message.reply_text("1080p Mode has been set", quote=True)
        cmd1.insert(0, "-pix_fmt yuv420p10 -preset veryfast -s 1920x1080 -crf 25 -c:a libopus -ab 128k -c:s copy -y")
                         
    @app.on_message(filters.incoming & filters.command(["restart", f"restart@{BOT_USERNAME}"]))
    async def restart_bot(app, message):
        await message.reply_text("Rebooting ...")
        quit(1)
        
    @app.on_message(filters.incoming & filters.command(["clear", f"clear@{BOT_USERNAME}"]))
    async def clear_queue(app, message):
        data.clear()
        await message.reply_text("Successfully cleared Queue ...")
         
    @app.on_message(filters.incoming & (filters.video | filters.document))
    async def handle_media(app, message):
        query = await message.reply_text("Added to Queue ⏰...\nPlease be patient, Compress will start soon", quote=True)
        data.append(message)
        if len(data) == 1:
            await query.delete()   
            await add_task(message)
            
    @app.on_message(filters.incoming & (filters.photo))
    async def handle_photo(app, message):
        os.system('rm -f thumb.jpg')
        await message.download(file_name='/app/thumb.jpg')
        await message.reply_text('Thumbnail Added')
        
    @app.on_message(filters.incoming & filters.command(["cancel", f"cancel@{BOT_USERNAME}"]))
    async def cancel_message(app, message):
        await incoming_cancel_message_f(app, message)

    @app.on_message(filters.incoming & filters.command(["eval", f"eval@{BOT_USERNAME}"]))
    async def eval_message(app, message):
        await eval_message_f(app, message)
        
    @app.on_message(filters.incoming & filters.command(["exec", f"exec@{BOT_USERNAME}"]))
    async def exec_message(app, message):
        await exec_message_f(app, message)
        
    @app.on_message(filters.incoming & filters.command(["stop", f"stop@{BOT_USERNAME}"]))
    async def stop_message(app, message):
        await on_task_complete()  
   
    @app.on_message(filters.incoming & filters.command(["help", f"help@{BOT_USERNAME}"]))
    async def help_command(app, message):
        help_text = (
            "Hi, I am Video Encoder bot\n\n"
            "➥ Send me your telegram files\n"
            "➥ I will encode them one by one as I have queue feature\n"
            "➥ Just send me the jpg/pic and it will be set as your custom thumbnail \n"
            "➥ For ffmpeg lovers - u can change crf by /eval crf.insert(0, 'crf value')\n"
            "➥ Join @Tellybots for bots \n\n"
            "🏷Maintained By: @Tellybots"
        )
        await message.reply_text(help_text, quote=True)
  
    @app.on_message(filters.incoming & filters.command(["log", f"log@{BOT_USERNAME}"]))
    async def log_message(app, message):
        await upload_log_file(app, message)

    @app.on_message(filters.incoming & filters.command(["ping", f"ping@{BOT_USERNAME}"]))
    async def ping_command(app, message):
        stt = dt.now()
        ed = dt.now()
        v = ts(int((ed - uptime).seconds) * 1000)
        ms = (ed - stt).microseconds / 1000
        p = f"🌋Pɪɴɢ = {ms}ms"
        await message.reply_text(v + "\n" + p)

    call_back_button_handler = CallbackQueryHandler(
        button
    )
    app.add_handler(call_back_button_handler)

    # run the application
    app.run()
