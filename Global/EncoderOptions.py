# Video Options Class
class VideoOptions:
    def __init__(self, pixel_format="yuv420p", codec="h264_nvenc", bitrate="10M", preset="fast"):
        self.pixel_format = pixel_format
        self.codec = codec
        self.bitrate = bitrate
        self.preset = preset

    def __str__(self):
        return f"Video Options: pixel_format={self.pixel_format}, codec={self.codec}, bitrate={self.bitrate}, preset={self.preset}"
# Audio Options Class
class AudioOptions:
    def __init__(self, codec="libmp3lame", bitrate="128k", sample_rate="48000", channel_layout="stereo"):
        self.codec = codec
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.channel_layout = channel_layout

    def __str__(self):
        return f"Audio Options: codec={self.codec}, bitrate={self.bitrate}, sample_rate={self.sample_rate}, channel_layout={self.channel_layout}"
# Mapping Options Class
class MappingOptions:
    def __init__(self, video_stream="0:v", audio_stream="0:1", subtitle_disabled=True):
        self.video_stream = video_stream
        self.audio_stream = audio_stream
        self.subtitle_disabled = subtitle_disabled

    def __str__(self):
        subtitle_status = "disabled" if self.subtitle_disabled else "enabled"
        return f"Mapping: video={self.video_stream}, audio={self.audio_stream}, subtitles={subtitle_status}"
# HLS Options Class
class HLSOptions:
    def __init__(self, segment_time=10, playlist_type="event", flags="append_list+delete_segments", segment_filename="segment_%03d.ts"):
        self.segment_time = segment_time
        self.playlist_type = playlist_type
        self.flags = flags
        self.segment_filename = segment_filename

    def __str__(self):
        return f"HLS Options: segment_time={self.segment_time}, playlist_type={self.playlist_type}, flags={self.flags}, segment_filename={self.segment_filename}"


