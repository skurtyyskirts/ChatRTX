with open("ChatRTX_APIs/ChatRTX/inference/trtllm/whisper/trt_whisper.py", "r") as f:
    content = f.readlines()

new_content = []
seen_dataclass = False
for line in content:
    if line.strip() == "import time":
        continue
    if line.strip() == "from dataclasses import dataclass":
        if seen_dataclass:
            continue
        seen_dataclass = True
    new_content.append(line)

with open("ChatRTX_APIs/ChatRTX/inference/trtllm/whisper/trt_whisper.py", "w") as f:
    f.writelines(new_content)
