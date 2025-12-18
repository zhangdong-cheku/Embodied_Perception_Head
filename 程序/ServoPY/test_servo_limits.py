# 舵机极限测试程序
# 这个程序会为每个舵机生成一个测试脚本，依次转到最大值和最小值
# 用于帮助理解每个舵机的物理运动方向

import json
import os

# 读取配置文件
base_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(base_dir, "servo_config.json")

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 舵机名称映射
servo_names = {
    0: "右下颚",
    1: "左下颚",
    2: "右上唇",
    3: "左上唇",
    4: "右下唇",
    5: "左下唇",
    6: "右上眼睑",
    7: "左上眼睑",
    8: "右下眼睑",
    9: "左下眼睑",
    10: "眼球水平",
    11: "眼球垂直",
    12: "右眉毛外舵机（眉梢）",
    13: "右眉毛内舵机（眉头）",
    14: "左眉毛外舵机（眉梢）",
    15: "左眉毛内舵机（眉头）"
}

# 生成测试脚本
test_script = "# 舵机极限测试脚本\n# 依次测试每个舵机的最大值和最小值\n# 请观察并记录每个动作代表的真实物理运动\n\n"

for servo_id in range(16):
    servo_name = servo_names.get(servo_id, f"舵机{servo_id}")
    min_angle = config.get(f"servo_{servo_id}_min", 0)
    max_angle = config.get(f"servo_{servo_id}_max", 180)
    
    test_script += f"# ============ {servo_name} (舵机{servo_id}) ============\n"
    test_script += f"# 当前测试: {servo_name}\n"
    test_script += f"# 配置: 最小值={min_angle}°, 最大值={max_angle}°\n\n"
    
    # 1. 转到最小值
    test_script += f"# 1. 转到最小值: {min_angle}°\n"
    test_script += f"舵机{servo_id} {min_angle}\n"
    test_script += "延时 2000\n\n"
    
    # 2. 转到最大值
    test_script += f"# 2. 转到最大值: {max_angle}°\n"
    test_script += f"舵机{servo_id} {max_angle}\n"
    test_script += "延时 2000\n\n"
    
    # 3. 回到当前中间值
    mid_angle = config.get(f"servo_{servo_id}_mid", 90)
    test_script += f"# 3. 回到当前中间值: {mid_angle}°\n"
    test_script += f"舵机{servo_id} {mid_angle}\n"
    test_script += "延时 1000\n\n"
    
    test_script += "# ==========================================\n\n"

# 保存测试脚本
test_script_path = os.path.join(base_dir, "表情脚本", "99_舵机极限测试.txt")
os.makedirs(os.path.dirname(test_script_path), exist_ok=True)

with open(test_script_path, 'w', encoding='utf-8') as f:
    f.write(test_script)

print(f"测试脚本已生成: {test_script_path}")
print("\n使用说明:")
print("1. 将此脚本加载到ZS_BOX.py的脚本编辑区")
print("2. 运行脚本，观察每个舵机的运动")
print("3. 记录每个舵机在最小值和最大值时的真实物理运动")
print("4. 例如: 右上眼睑(舵机6) - 最小值55°=闭合，最大值148°=睁开")
print("\n请将记录的信息提供给我，以便生成更合理的中间值。")