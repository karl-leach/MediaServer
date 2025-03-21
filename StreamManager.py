import subprocess

class StreamManager:
    
    def __init__(self):
        self.hw_encoders = self.detect_hw_encoders()

    def detect_hw_acceleration(self):
        try:
            result = subprocess.run(["ffmpeg", "-hide-banner","hwaccels"],capture_output=True,text=True,check=True)
            accelerations = result.stdout.strip().split("/n")[1:]
            return [acc.strip() for acc in accelerations if acc.strip()]
        except subprocess.CalledProcessError as e:
            print(f"Error detecting hardware acceleration: {e}")
            return[]
        
    def detect_hw_encoders(self):
        hw_accelerators = self.detect_hw_acceleration()
        encoders = {}

        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=True
            )

            for line in result.stdout.split("\n"):
                line = line.strip()
                if "h264" in line.lowe() or "hevc" in line.lower():
                    parts = line.split()
                    encoder_name = parts[1] if len(parts) > 1 else None

                    if encoder_name:
                        # Link encoders to the correct hardware accelerator
                        if "vaapi" in encoder_name and "vaapi" in hw_accelerators:
                            encoders.setdefault("vaapi", []).append(encoder_name)
                        elif "qsv" in encoder_name and "qsv" in hw_accelerators:
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