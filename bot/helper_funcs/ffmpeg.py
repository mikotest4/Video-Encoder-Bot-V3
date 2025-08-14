from bot.config import Config
import asyncio
import os
import time
import re
import json
import subprocess
import math
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.display_progress import (
  TimeFormatter
)
from bot.localisation import Localisation
from bot import (
    FINISHED_PROGRESS_STR,
    UN_FINISHED_PROGRESS_STR,
    DOWNLOAD_LOCATION,
    crf,
    watermark,
    pid_list,
    resolution,
    bit,
    preset
)

async def convert_video(video_file, output_directory, total_time, bot, message, chan_msg):
    # https://stackoverflow.com/a/13891070/4723940
    kk = video_file.split("/")[-1]
    aa = kk.split(".")[-1]
    out_put_file_name = kk.replace(f".{aa}", " [FIERCENETWORK].mkv")
    #out_put_file_name = video_file + "_compressed" + ".mkv"
    progress = output_directory + "/" + "progress.txt"
    with open(progress, 'w') as f:
      pass
    ##  -metadata title='DarkEncodes [Join t.me/AnimesInLowSize]' -vf drawtext=fontfile=Italic.ttf:fontsize=20:fontcolor=black:x=15:y=15:text='Dark Encodes'
    ##"-metadata", "title=@SenpaiAF", "-vf", "drawtext=fontfile=njnaruto.ttf:fontsize=20:fontcolor=black:x=15:y=15:text=" "Dark Encodes",
     ## -vf eq=gamma=1.4:saturation=1.4
     ## lol 😂
    crf.append("26.2 -map 0")
    resolution.append("1280x720")
    bit.append("yuv420p")
    preset.append("veryfast")
    watermark.append('-vf "drawtext=fontfile=font.ttf:fontsize=25:fontcolor=white:bordercolor=black@0.50:x=w-tw-10:y=10:box=1:boxcolor=black@0.5:boxborderw=6:text=FIERCENETWORK"')
    file_genertor_command = f'ffmpeg -hide_banner -loglevel quiet -progress "{progress}" -i "{video_file}" -c:v libx265  -crf {crf[0]} -c:s copy -preset fast -pix_fmt yuv420p10le -vf scale=1280:trunc(ow/a/2)*2 -x265-params no-info=1 -metadata title="Moviez Café™ | 720p.10bit.HEVC.x265"  -metadata:s:v title="W∆L13R - 720p/ 10bit/ HEVC"  -metadata:s:a title="Opus ~ W∆L13R" -metadata:s:s title="English ~ W∆L13R" -c:a libopus -b:a 64k "{out_put_file_name}" -y'
 #For Ffmpeg Use
    COMPRESSION_START_TIME = time.time()
    process = await asyncio.create_subprocess_shell(
          file_genertor_command,
          # stdout must a pipe to be accessible as process.stdout
           stdout=asyncio.subprocess.PIPE,
           stderr=asyncio.subprocess.PIPE,
          )
    #stdout, stderr = await process.communicate()
    
    Config.LOGGER.info("ffmpeg_process: "+str(process.pid))
    pid_list.insert(0, process.pid)
    status = output_directory + "/status.json"
    with open(status, 'r+') as f:
      statusMsg = json.load(f)
      statusMsg['pid'] = process.pid
      statusMsg['message'] = message.id  # Fixed: changed from message.message_id to message.id
      f.seek(0)
      json.dump(statusMsg,f,indent=2)
    # os.kill(process.pid, 9)
    isDone = False
    while process.returncode != 0:
      await asyncio.sleep(3)
      with open(DOWNLOAD_LOCATION + "/progress.txt", 'r+') as file:
        text = file.read()
        frame = re.findall("frame=(\d+)", text)
        time_in_us=re.findall("out_time_ms=(\d+)", text)
        progress_regex=re.findall("progress=(\w+)", text)
        speed=re.findall("speed=(\d+\.?\d*)", text)
        if len(frame):
          frame = int(frame[-1])
        else:
          frame = 1;
        if len(speed):
          speed = speed[-1]
        else:
          speed = 1;
        if len(time_in_us):
          time_in_us = time_in_us[-1]
        else:
          time_in_us = 1;
        if len(progress_regex):
          if progress_regex[-1] == "end":
            Config.LOGGER.info(progress_regex[-1])
            isDone = True
            break
        execution_time = TimeFormatter((time.time() - COMPRESSION_START_TIME)*1000)
        elapsed_time = int(time_in_us)/1000000
        difference = math.floor( (total_time - elapsed_time) / float(speed) )
        ETA = "-"
        if difference > 0:
          ETA = TimeFormatter(difference*1000)
        percentage = math.floor(elapsed_time * 100 / total_time)
        progress_str = "📊 <b>Progress:</b> {0}%\n[{1}{2}]".format(
            round(percentage, 2),
            ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
            ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))])
            )
        stats = f'📦️ <b>Encoding Is In Progress</b>\n\n'
        try:
          await message.edit_text(
            text=stats,
            reply_markup=InlineKeyboardMarkup(
                [
                    [ 
                        InlineKeyboardButton('❌ Cancel ❌', callback_data='fuckingdo') # Fixed callback data
                    ]
                ]
            )
          )
        except:
            pass
        try:
          await chan_msg.edit_text(text=stats)  # Fixed variable name from 'bug' to 'chan_msg'
        except:
          pass        
        
        
    stdout, stderr = await process.communicate()
    r = stderr.decode()
    try:
        if r:  # Fixed variable name from 'er' to 'r'
           await message.edit_text(str(r) + "\n\n**ERROR** Contact @SenpaiAF")
           os.remove(video_file)  # Fixed variable name from 'videofile' to 'video_file'
           os.remove(out_put_file_name)
           return None
    except BaseException:
            pass
    #if( not isDone):
      #return None
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    Config.LOGGER.info(e_response)
    Config.LOGGER.info(t_response)
    del pid_list[0]
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

async def media_info(saved_file_path):
  process = subprocess.Popen(
    [
      'ffmpeg', 
      "-hide_banner", 
      '-i', 
      saved_file_path
    ], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT
  )
  stdout, stderr = process.communicate()
  output = stdout.decode().strip()
  duration = re.search("Duration:\s*(\d*):(\d*):(\d+\.?\d*)[\s\w*$]",output)
  bitrates = re.search("bitrate:\s*(\d+)[\s\w*$]",output)
  
  if duration is not None:
    hours = int(duration.group(1))
    minutes = int(duration.group(2))
    seconds = math.floor(float(duration.group(3)))
    total_seconds = ( hours * 60 * 60 ) + ( minutes * 60 ) + seconds
  else:
    total_seconds = None
  if bitrates is not None:
    bitrate = bitrates.group(1)
  else:
    bitrate = None
  return total_seconds, bitrate
  
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = os.path.join(
        output_directory,
        str(time.time()) + ".jpg"
    )
    if video_file.upper().endswith(("MKV", "MP4", "WEBM")):
        file_genertor_command = [
            "ffmpeg",
            "-ss",
            str(ttl),
            "-i",
            video_file,
            "-vframes",
            "1",
            out_put_file_name
        ]
        
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
    #
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None
# senpai I edited this,  maybe if it is wrong correct it
