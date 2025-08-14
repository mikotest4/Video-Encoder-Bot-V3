import datetime
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)
import os, time, asyncio, json
from bot.localisation import Localisation
from bot import (
  DOWNLOAD_LOCATION,
  LOG_CHANNEL,
  UPDATES_CHANNEL,
  SESSION_NAME,
  data,
  app  
)
from bot.helper_funcs.ffmpeg import (
  convert_video,
  media_info,
  take_screen_shot
)
from bot.helper_funcs.display_progress import (
  progress_for_pyrogram,
  TimeFormatter,
  humanbytes
)
from bot.config import Config
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid
from pyrogram.enums import ParseMode

os.system("wget https://telegra.ph/file/5c4635e173e7407694a63.jpg -O thumb.jpg")

CURRENT_PROCESSES = {}
CHAT_FLOOD = {}
broadcast_ids = {}
bot = app        

async def incoming_start_message_f(bot, update):
    """/start command"""
    await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.START_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('SOURCE CODE', url='https://t.me/tellybots')
                ]
            ]
        ),
        reply_to_message_id=update.id,
    )
    
async def incoming_compress_message_f(update):
    """/compress command"""
    isAuto = True
    d_start = time.time()
    c_start = time.time()
    u_start = time.time()
    status = DOWNLOAD_LOCATION + "/status.json"
    
    sent_message = await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.DOWNLOAD_START,
        reply_to_message_id=update.id
    )
    
    chat_id = LOG_CHANNEL
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
    bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
    bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
    now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
    download_start = await bot.send_message(
        chat_id=chat_id, 
        text=f"**Bot Become Busy Now !!** \n\nDownload Started at `{now}`", 
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        d_start = time.time()
        status = DOWNLOAD_LOCATION + "/status.json"
        with open(status, 'w') as f:
            statusMsg = {
                'running': True,
                'message': sent_message.id
            }
            json.dump(statusMsg, f, indent=2)
            
        video = await bot.download_media(
            message=update,  
            progress=progress_for_pyrogram,
            progress_args=(
                bot,
                Localisation.DOWNLOAD_START,
                sent_message,
                d_start
            )
        )
        saved_file_path = video
        Config.LOGGER.info(saved_file_path)  
        Config.LOGGER.info(video)
        
        if video is None:
            try:
                await sent_message.edit_text(
                    text="Download stopped"
                )
                chat_id = LOG_CHANNEL
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
                bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
                await bot.send_message(
                    chat_id=chat_id, 
                    text=f"**Download Stopped, Bot is Free Now !!** \n\nProcess Done at `{now}`", 
                    parse_mode=ParseMode.MARKDOWN
                )
                await download_start.delete()
            except:
                pass
            Config.LOGGER.info("Download stopped")
            return
            
    except (ValueError) as e:
        try:
            await sent_message.edit_text(
                text=str(e)
            )
        except:
            pass
            
    try:
        await sent_message.edit_text(                
            text=Localisation.SAVED_RECVD_DOC_FILE                
        )
    except:
        pass     
  
    if os.path.exists(saved_file_path):
        downloaded_time = TimeFormatter((time.time() - d_start)*1000)
        duration, bitrate = await media_info(saved_file_path)
        
        if duration is None or bitrate is None:
            try:
                await sent_message.edit_text(                
                    text="⚠️ Getting video meta data failed ⚠️"                
                )
                chat_id = LOG_CHANNEL
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
                bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
                await bot.send_message(
                    chat_id=chat_id, 
                    text=f"**Download Failed, Bot is Free Now !!** \n\nProcess Done at `{now}`", 
                    parse_mode=ParseMode.MARKDOWN
                )
                await download_start.delete()
            except:
                pass          
            return
            
        thumb_image_path = await take_screen_shot(
            saved_file_path,
            os.path.dirname(os.path.abspath(saved_file_path)),
            (duration / 2)
        )
        
        chat_id = LOG_CHANNEL
        utc_now = datetime.datetime.utcnow()
        ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
        ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
        bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
        bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
        now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
        await download_start.delete()
        compress_start = await bot.send_message(
            chat_id=chat_id, 
            text=f"**Compressing Video ...** \n\nProcess Started at `{now}`", 
            parse_mode=ParseMode.MARKDOWN
        )
        
        await sent_message.edit_text(                    
            text=Localisation.COMPRESS_START                    
        )
        
        c_start = time.time()
        o = await convert_video(
            video, 
            DOWNLOAD_LOCATION, 
            duration, 
            bot, 
            sent_message, 
            compress_start
        )
        
        compressed_time = TimeFormatter((time.time() - c_start)*1000)
        Config.LOGGER.info(o)
        
        if o == 'stopped':
            return
            
        if o is not None:
            chat_id = LOG_CHANNEL
            utc_now = datetime.datetime.utcnow()
            ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
            ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
            bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
            bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
            now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
            await compress_start.delete()
            upload_start = await bot.send_message(
                chat_id=chat_id, 
                text=f"**Uploading Video ...** \n\nProcess Started at `{now}`", 
                parse_mode=ParseMode.MARKDOWN
            )
            
            await sent_message.edit_text(                    
                text=Localisation.UPLOAD_START,                    
            )
            
            u_start = time.time()
            caption = Localisation.COMPRESS_SUCCESS.replace('{}', downloaded_time, 1).replace('{}', compressed_time, 1)
            
            upload = await bot.send_document(
                chat_id=update.chat.id,
                document=o,
                caption=caption,
                force_document=True,
                thumb="thumb.jpg",
                reply_to_message_id=update.id,
                progress=progress_for_pyrogram,
                progress_args=(
                    bot,
                    Localisation.UPLOAD_START,
                    sent_message,
                    u_start
                )
            )
            
            if upload is None:
                try:
                    await sent_message.edit_text(
                        text="Upload stopped"
                    )
                    chat_id = LOG_CHANNEL
                    utc_now = datetime.datetime.utcnow()
                    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                    bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
                    bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                    now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
                    await bot.send_message(
                        chat_id=chat_id, 
                        text=f"**Upload Stopped, Bot is Free Now !!** \n\nProcess Done at `{now}`", 
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await upload_start.delete()
                except:
                    pass
                Config.LOGGER.info("Upload stopped")
                return
                
            uploaded_time = TimeFormatter((time.time() - u_start)*1000)
            
            try:
                await sent_message.delete()
            except:
                pass
                
            chat_id = LOG_CHANNEL
            utc_now = datetime.datetime.utcnow()
            ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
            ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
            bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
            bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
            now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
            await upload_start.delete()
            await bot.send_message(
                chat_id=chat_id, 
                text=f"**Successfully Completed Process, Bot is Free Now !!** \n\nProcess Done at `{now}`", 
                parse_mode=ParseMode.MARKDOWN
            )
            
        else:
            try:
                await sent_message.edit_text(
                    text="❌ Compression failed"
                )
                chat_id = LOG_CHANNEL
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
                bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
                await bot.send_message(
                    chat_id=chat_id, 
                    text=f"**Compression Failed, Bot is Free Now !!** \n\nProcess Done at `{now}`", 
                    parse_mode=ParseMode.MARKDOWN
                )
                await compress_start.delete()
            except:
                pass
                
        # Cleanup files
        try:
            os.remove(saved_file_path)
            if o and os.path.exists(o):
                os.remove(o)
            if thumb_image_path and os.path.exists(thumb_image_path):
                os.remove(thumb_image_path)
        except:
            pass


async def incoming_cancel_message_f(app, message):
    """/cancel command"""
    try:
        await message.reply_text("Process cancelled successfully!")
    except:
        pass
