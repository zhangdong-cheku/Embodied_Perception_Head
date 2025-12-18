# 根据用户提供的舵机物理运动信息重新计算中间值
import json
import os

# 用户提供的舵机数据
servos_data = [
    {"id": 0, "name": "右下颚", "min": 64, "max": 85, "max_state": "张嘴"},
    {"id": 1, "name": "左下颚", "min": 0, "max": 180, "max_state": "张嘴"},
    {"id": 2, "name": "右上唇", "min": 83, "max": 124, "max_state": "上扬"},
    {"id": 3, "name": "左上唇", "min": 38, "max": 75, "max_state": "下垂"},
    {"id": 4, "name": "右下唇", "min": 82, "max": 137, "max_state": "上扬"},
    {"id": 5, "name": "左下唇", "min": 0, "max": 65, "max_state": "下垂"},
    {"id": 6, "name": "右上眼睑", "min": 55, "max": 148, "max_state": "睁开"},
    {"id": 7, "name": "左上眼睑", "min": 25, "max": 106, "max_state": "闭合"},
    {"id": 8, "name": "右下眼睑", "min": 67, "max": 128, "max_state": "闭合"},
    {"id": 9, "name": "左下眼睑", "min": 53, "max": 123, "max_state": "睁开"},
    {"id": 10, "name": "眼球水平", "min": 71, "max": 113, "max_state": "上转"},
    {"id": 11, "name": "眼球垂直", "min": 52, "max": 109, "max_state": "左转"},
    {"id": 12, "name": "右眉毛外舵机（眉梢）", "min": 38, "max": 76, "max_state": "上扬"},
    {"id": 13, "name": "右眉毛内舵机（眉头）", "min": 35, "max": 89, "max_state": "下垂"},
    {"id": 14, "name": "左眉毛外舵机（眉梢）", "min": 104, "max": 126, "max_state": "下垂"},
    {"id": 15, "name": "左眉毛内舵机（眉头）", "min": 100, "max": 142, "max_state": "上扬"}
]

# 分析并计算新的中间值
new_mid_values = []

for servo in servos_data:
    servo_id = servo["id"]
    min_angle = servo["min"]
    max_angle = servo["max"]
    max_state = servo["max_state"]
    name = servo["name"]
    
    # 根据物理状态推断运动方向并计算合理的中间值
    if "眼睑" in name:
        # 眼睑舵机 - 中间值应该是自然睁开状态
        if max_state == "睁开":
            # 最大值是睁开，最小值是闭合，中间值应该偏向睁开方向
            mid = int(min_angle + (max_angle - min_angle) * 0.7)
        elif max_state == "闭合":
            # 最大值是闭合，最小值是睁开，中间值应该偏向睁开方向
            mid = int(max_angle - (max_angle - min_angle) * 0.7)
        else:
            # 默认取中间值
            mid = int((min_angle + max_angle) / 2)
    
    elif "眉毛" in name:
        # 眉毛舵机 - 中间值应该是自然放松状态
        if max_state == "上扬":
            # 最大值是上扬，最小值是下垂，中间值取中间位置
            mid = int((min_angle + max_angle) / 2)
        elif max_state == "下垂":
            # 最大值是下垂，最小值是上扬，中间值取中间位置
            mid = int((min_angle + max_angle) / 2)
        else:
            mid = int((min_angle + max_angle) / 2)
    
    elif "下颚" in name or "唇" in name:
        # 下颚和嘴唇舵机 - 中间值应该是自然闭合状态
        if max_state == "张嘴":
            # 最大值是张嘴，最小值是闭嘴，中间值应该偏向闭嘴方向
            mid = int(min_angle + (max_angle - min_angle) * 0.2)
        elif max_state == "上扬":
            # 最大值是上扬，最小值是下垂，中间值取中间偏下位置
            mid = int(min_angle + (max_angle - min_angle) * 0.4)
        elif max_state == "下垂":
            # 最大值是下垂，最小值是上扬，中间值取中间偏上位置
            mid = int(max_angle - (max_angle - min_angle) * 0.4)
        else:
            mid = int((min_angle + max_angle) / 2)
    
    elif "眼球" in name:
        # 眼球舵机 - 中间值应该是正视前方状态
        # 假设水平和垂直舵机的中间值是正视前方
        mid = int((min_angle + max_angle) / 2)
    
    else:
        # 默认取中间值
        mid = int((min_angle + max_angle) / 2)
    
    # 确保中间值在安全范围内
    mid = max(min_angle, min(max_angle, mid))
    
    new_mid_values.append(mid)
    print(f"舵机{servo_id} ({name}): 最小值={min_angle}, 最大值={max_angle}, 物理状态={max_state}, 新中间值={mid}")

# 读取原始配置文件
base_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(base_dir, "servo_config.json")

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 更新中间值
for i, mid_value in enumerate(new_mid_values):
    config[f"servo_{i}_mid"] = mid_value

# 保存更新后的配置文件
updated_config_file = os.path.join(base_dir, "servo_config_updated.json")
with open(updated_config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n更新后的配置已保存到: {updated_config_file}")
print("\n使用说明：")
print("1. 检查生成的中间值是否合理")
print("2. 如果需要微调，可以直接编辑配置文件")
print("3. 可以将更新后的配置文件重命名为 servo_config.json 以应用到系统中")