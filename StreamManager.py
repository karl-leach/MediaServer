import subprocess
import os
import platform
from Global.EncoderOptions import *
import threading
from typing import Dict

class StreamManager:
    
    

    def __init__(self):
        self.streams: Dict[str, threading.Thread] = {}
        self.cancellation_flags: Dict[str, threading.Event] = {}
        if os.name == 'nt':
            self.ffmpeg_command = ".\\FFMPEG\\ffmpeg.exe"
        else:
            self.ffmpeg_command = "ffmpeg"
        self.hw_encoders = self.detect_hw_encoders()
        self.EncoderType = next(iter(self.hw_encoders.values()))[0] #Default Encoder


    def detect_hw_acceleration(self):
        try:
            result = subprocess.run([self.ffmpeg_command, "-hide_banner","-hwaccels"],capture_output=True,text=True,check=True)
            accelerations = result.stdout.strip().split("\n")[1:]
            return [acc.strip() for acc in accelerations if acc.strip()]
        except subprocess.CalledProcessError as e:
            print(f"Error detecting hardware acceleration: {e}")
            return[]
        
    def detect_hw_encoders(self):
        hw_accelerators = self.detect_hw_acceleration()
        encoders = {}

        try:
            result = subprocess.run(
                [self.ffmpeg_command, "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=True
            )

            for line in result.stdout.split("\n"):
                line = line.strip()
                if "h264" in line.lower() or "hevc" in line.lower():
                    parts = line.split()
                    encoder_name = parts[1] if len(parts) > 1 else None

                    if encoder_name:
                        # Link encoders to the correct hardware accelerator
                        if "vaapi" in encoder_name and "vaapi" in hw_accelerators and os.name != 'nt':
                            encoders.setdefault("vaapi", []).append(encoder_name)
                        elif "qsv" in encoder_name and "qsv" in hw_accelerators and "intel" in platform.processor().lower():
                            encoders.setdefault("qsv", []).append(encoder_name)
                        elif "nvenc" in encoder_name and "cuda" in hw_accelerators:
                            encoders.setdefault("cuda", []).append(encoder_name)
                        elif "libx264" in encoder_name or "libx265" in encoder_name:
                            encoders.setdefault("software", []).append(encoder_name)

        except subprocess.CalledProcessError as e:
            print(f"Error detecting encoders: {e}")

        return encoders
    
    def get_system_capabilities(self):
        return self.hw_encoders
    
    def set_encoder_type(self,encoder):
        for category,encoder_list in self.hw_encoders.items():
            if encoder in encoder_list:
                self.EncoderType = encoder
                

    def start_video_stream(self,instance:str, input:str, output:str, video_options:VideoOptions, audio_options:AudioOptions, mapping_options:MappingOptions, hls_options:HLSOptions):
        command = f"{self.ffmpeg_command} -i {input} -vf format={video_options.pixel_format} -c:v {video_options.codec} " \
                  f"-b:v {video_options.bitrate} -preset {video_options.preset} -map {mapping_options.video_stream} " \
                  f"-map {mapping_options.audio_stream} {'-sn' if mapping_options.subtitle_disabled else ''} " \
                  f"-c:a {audio_options.codec} -b:a {audio_options.bitrate} -ar {audio_options.sample_rate} " \
                  f"-channel_layout {audio_options.channel_layout} -hls_time {hls_options.segment_time} " \
                  f"-hls_playlist_type {hls_options.playlist_type} -hls_flags {hls_options.flags} " \
                  f"-hls_segment_filename \"{output}{hls_options.segment_filename}\" {output}"
        
        if instance in self.streams:
            raise ValueError(f"Instance {instance} is already running")
        
        cancel_event = threading.Event()
        self.cancellation_flags[instance] = cancel_event

        def run_ffmpeg():
            print(f"Starting FFMpeg with command {command}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
            while not cancel_event.is_set():
                if process.poll() is not None:
                    break;

            if cancel_event.is_set():
                process.terminate()
                print(f"Ending FFMpeg Process")
        
        thread = threading.Thread(target=run_ffmpeg,daemon=True)
        self.streams[instance] = thread;
        thread.start()
        print(f"Instance {instance} started")
    

    def cancel_video_stream(self, instance:str):
        if instance not in self.streams:
            raise ValueError(f"Instance {instance} is not running")
        self.cancellation_flags[instance].set()
        self.streams[instance].join()
        del self.streams[instance]
        del self.cancellation_flags[instance]

            


        