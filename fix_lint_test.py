with open("ChatRTX_APIs/tests/test_model_manager_util.py", "r") as f:
    content = f.readlines()

new_content = []
for line in content:
    if line.strip() == "import io":
        continue
    new_content.append(line)

with open("ChatRTX_APIs/tests/test_model_manager_util.py", "w") as f:
    f.writelines(new_content)
