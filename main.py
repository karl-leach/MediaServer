from StreamManager import StreamManager


stream_man = StreamManager()

capabilities = stream_man.get_system_capabilities()
print(capabilities)