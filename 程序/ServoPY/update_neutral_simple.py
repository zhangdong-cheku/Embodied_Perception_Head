import os
import json

# 读取配置文件
config_path = os.path.join(os.path.dirname(__file__), 'servo_config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 使用列表构建脚本内容，避免字符串拼接问题
content_lines = []
content_lines.append("# ============ 中性表情 ============")
content_lines.append("# 所有舵机在中间值位置")
content_lines.append("# 这是所有表情的基准状态")
content_lines.append("")

# 添加每个舵机的中间值
for i in range(16):
    mid_key = f"servo_{i}_mid"
    if mid_key in config:
        value = config[mid_key]
        content_lines.append(f"舵机{i} {value}")
        print(f"添加舵机{i}: {value}")
    else:
        print(f"警告: 配置文件中没有找到 {mid_key}")

# 添加延时
content_lines.append("延时 1000")

# 连接所有行
neutral_content = "\n".join(content_lines)

# 写入文件
output_path = os.path.join(os.path.dirname(__file__), '表情脚本', '01_中性表情.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(neutral_content)

print("中性表情脚本已更新！")
print("生成的脚本内容：")
print(neutral_content)
