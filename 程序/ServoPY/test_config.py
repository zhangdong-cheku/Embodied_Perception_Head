import os
import json

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"当前脚本目录: {script_dir}")

# 配置文件路径
config_path = os.path.join(script_dir, 'servo_config.json')
print(f"配置文件路径: {config_path}")
print(f"配置文件存在: {os.path.exists(config_path)}")

# 读取配置文件
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("配置文件内容:")
    for key, value in config.items():
        if 'mid' in key:
            print(f"{key}: {value}")
