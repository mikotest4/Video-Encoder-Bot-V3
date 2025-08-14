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

def humanbytes(size):
    """Convert bytes to human readable format"""
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def create_progress_bar(percentage, length=20):
    """Create a visual progress bar"""
    filled_length = int(length * percentage // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}]"

async def get_video_codec(video_file):
    """Get the original video codec of the file"""
    try:
        process = subprocess.Popen(
            ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', video_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        codec = stdout.decode().strip()
        return codec if codec else 'h264'
    except:
        return 'h264'  # Default fallback

async def convert_video(video_file, output_directory, total_time, bot, message, chan_msg):
    # https://stackoverflow.com/a/13891070/4723940
    kk = video_file.split("/")[-1]
    aa = kk.split(".")[-1]
    out_put_file_name = kk.replace(f".{aa}", " [COMPRESSED].mkv")
    progress = output_directory + "/" + "progress.txt"
    with open(progress, 'w') as f:
      pass
    
    # Get original file size and codec
    try:
        original_size = os.path.getsize(video_file)
        original_codec = await get_video_codec(video_file)
    except:
        original_size = 0
        original_codec = 'h264'
    
    # Clear existing settings
    crf.clear()
    resolution.clear()
    bit.clear()
    preset.clear()
    watermark.clear()
    
    # Set default values
    crf.append("23")  # Better quality, lower number = higher quality
    
    # Determine codec settings based on original codec
    if original_codec.lower() in ['h264', 'avc']:
        codec_setting = 'libx264'
        pixel_format = 'yuv420p'
        codec_name = 'H.264/AVC'
    elif original_codec.lower() in ['h265', 'hevc']:
        codec_setting = 'libx265'
        pixel_format = 'yuv420p10le'
        codec_name = 'H.265/HEVC'
    elif original_codec.lower() in ['vp9']:
        codec_setting = 'libvpx-vp9'
        pixel_format = 'yuv420p'
        codec_name = 'VP9'
    elif original_codec.lower() in ['av1']:
        codec_setting = 'libaom-av1'
        pixel_format = 'yuv420p'
        codec_name = 'AV1'
    else:
        # Keep original codec if supported, otherwise use h264
        codec_setting = 'copy' if original_codec in ['h264', 'h265', 'vp9'] else 'libx264'
        pixel_format = 'yuv420p'
        codec_name = f'Original ({original_codec.upper()})'
    
    # Build FFmpeg command without watermark and keeping original format
    if codec_setting == 'copy':
        # Just copy the video stream without re-encoding
        file_genertor_command = f'ffmpeg -hide_banner -loglevel quiet -progress "{progress}" -i "{video_file}" -c:v copy -c:a copy -c:s copy "{out_put_file_name}" -y'
    else:
        # Re-encode with same codec but compress
        file_genertor_command = f'ffmpeg -hide_banner -loglevel quiet -progress "{progress}" -i "{video_file}" -c:v {codec_setting} -crf {crf[0]} -c:a copy -c:s copy -preset medium -pix_fmt {pixel_format} -movflags +faststart "{out_put_file_name}" -y'
 
    COMPRESSION_START_TIME = time.time()
    process = await asyncio.create_subprocess_shell(
          file_genertor_command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
          )
    
    Config.LOGGER.info("ffmpeg_process: "+str(process.pid))
    Config.LOGGER.info(f"Using codec: {codec_setting} (Original: {original_codec})")
    pid_list.insert(0, process.pid)
    status = output_directory + "/status.json"
    with open(status, 'r+') as f:
      statusMsg = json.load(f)
      statusMsg['pid'] = process.pid
      statusMsg['message'] = message.id
      f.seek(0)
      json.dump(statusMsg,f,indent=2)
    
    isDone = False
    last_update_time = 0
    
    while process.returncode != 0:
      await asyncio.sleep(3)
      current_time = time.time()
      
      # Only update every 5 seconds to avoid rate limiting
      if current_time - last_update_time < 5:
          continue
      
      try:
          with open(DOWNLOAD_LOCATION + "/progress.txt", 'r+') as file:
            text = file.read()
            frame = re.findall("frame=(\d+)", text)
            time_in_us=re.findall("out_time_ms=(\d+)", text)
            progress_regex=re.findall("progress=(\w+)", text)
            speed=re.findall("speed=(\d+\.?\d*)", text)
            bitrate=re.findall("bitrate=(\d+\.?\d*\w*bits/s)", text)
            
            if len(frame):
              frame = int(frame[-1])
            else:
              frame = 1
              
            if len(speed):
              speed = float(speed[-1])
            else:
              speed = 1
              
            if len(time_in_us):
              time_in_us = int(time_in_us[-1])
            else:
              time_in_us = 1
              
            if len(bitrate):
              current_bitrate = bitrate[-1]
            else:
              current_bitrate = "N/A"
              
            if len(progress_regex):
              if progress_regex[-1] == "end":
                Config.LOGGER.info(progress_regex[-1])
                isDone = True
                break
                
            # Calculate progress
            elapsed_time = int(time_in_us)/1000000
            percentage = min(100, max(0, (elapsed_time / total_time) * 100))
            
            # Calculate ETA
            if speed > 0:
                remaining_time = (total_time - elapsed_time) / speed
                ETA = TimeFormatter(remaining_time * 1000) if remaining_time > 0 else "00:00:00"
            else:
                ETA = "Calculating..."
            
            # Elapsed time
            execution_time = TimeFormatter((current_time - COMPRESSION_START_TIME) * 1000)
            
            # Progress bar
            progress_bar = create_progress_bar(percentage, 20)
            
            # Current output file size (if exists)
            current_size = 0
            if os.path.exists(out_put_file_name):
                try:
                    current_size = os.path.getsize(out_put_file_name)
                except:
                    current_size = 0
            
            # Format the progress message
            stats = f"""🎬 <b>COMPRESSING VIDEO</b>

📊 <b>Progress:</b> {percentage:.1f}%
{progress_bar}

⏱ <b>Time Info:</b>
┣ Elapsed: {execution_time}
┣ ETA: {ETA}
┗ Speed: {speed}x

📈 <b>Processing Info:</b>
┣ Frame: {frame:,}
┣ Bitrate: {current_bitrate}
┗ Current Size: {humanbytes(current_size)}

🎥 <b>Video Info:</b>
┣ Original Codec: {original_codec.upper()}
┣ Output Codec: {codec_name}
┗ Original Size: {humanbytes(original_size)}

🔄 <b>Status:</b> Compressing without watermark...
"""
            
            try:
              await message.edit_text(
                text=stats,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [ 
                            InlineKeyboardButton('❌ Cancel Process ❌', callback_data='fuckingdo')
                        ]
                    ]
                )
              )
              last_update_time = current_time
            except Exception as e:
                Config.LOGGER.info(f"Error updating message: {e}")
                
            try:
              # Update channel message with simpler format
              channel_stats = f"""🎬 <b>VIDEO COMPRESSION</b>

📊 Progress: {percentage:.1f}%
{progress_bar}

⏱ ETA: {ETA}
🚀 Speed: {speed}x
🎥 Codec: {codec_name}
📈 Frame: {frame:,}
"""
              await chan_msg.edit_text(text=channel_stats)
            except Exception as e:
                Config.LOGGER.info(f"Error updating channel message: {e}")
                
      except Exception as e:
          Config.LOGGER.info(f"Error reading progress: {e}")
          await asyncio.sleep(2)
        
    stdout, stderr = await process.communicate()
    r = stderr.decode()
    
    try:
        if r and "error" in r.lower():
           await message.edit_text(str(r) + "\n\n**ERROR** Contact Support")
           if os.path.exists(video_file):
               os.remove(video_file)
           if os.path.exists(out_put_file_name):
               os.remove(out_put_file_name)
           return None
    except BaseException:
            pass
            
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    Config.LOGGER.info(e_response)
    Config.LOGGER.info(t_response)
    
    if pid_list:
        del pid_list[0]
        
    if os.path.lexists(out_put_file_name):
        # Show completion message
        final_size = os.path.getsize(out_put_file_name)
        compression_ratio = ((original_size - final_size) / original_size * 100) if original_size > 0 else 0
        
        completion_stats = f"""✅ <b>COMPRESSION COMPLETED!</b>

📊 <b>Compression Summary:</b>
┣ Original: {humanbytes(original_size)}
┣ Compressed: {humanbytes(final_size)}
┗ Space Saved: {compression_ratio:.1f}%

🎥 <b>Video Details:</b>
┣ Original Codec: {original_codec.upper()}
┣ Output Codec: {codec_name}
┗ Quality: High (No Watermark)

⏱ <b>Total Time:</b> {TimeFormatter((time.time() - COMPRESSION_START_TIME) * 1000)}

🎬 <b>Ready for upload...</b>
"""
        
        try:
            await message.edit_text(completion_stats)
        except:
            pass
            
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
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
    
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None
