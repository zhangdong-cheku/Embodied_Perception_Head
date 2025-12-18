import os
import json

# 读取最新的舵机配置
def load_servo_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

# 获取每个舵机的中间值
def get_servo_mid_values(config):
    mid_values = {}
    for i in range(16):
        mid_key = f"servo_{i}_mid"
        if mid_key in config:
            mid_values[i] = config[mid_key]
        else:
            # 如果没有找到中间值，使用默认值90
            mid_values[i] = 90
    return mid_values

# 更新表情脚本
def update_expression_script(file_path, mid_values):
    try:
        print(f"\n正在处理文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated_lines = []
        servo_lines = {}  # 存储每个舵机的最新行
        delay_line = None  # 存储延时命令行
        
        # 第一遍：收集现有行和更新舵机角度
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                # 保留注释行
                updated_lines.append(line)
            elif line.startswith("延时"):
                # 保存延时命令行
                delay_line = line
            elif line.startswith("舵机"):
                # 解析舵机行
                parts = line.split()
                if len(parts) == 2:
                    servo_info = parts[0]
                    # 正确提取舵机ID，例如"舵机11" -> 11
                    servo_id = int(servo_info[2:])  # 从第三个字符开始提取数字部分
                    if servo_id in mid_values:
                        # 更新舵机角度
                        new_line = f"舵机{servo_id} {mid_values[servo_id]}"
                        servo_lines[servo_id] = new_line
            else:
                # 保留其他行
                updated_lines.append(line)
        
        # 第二遍：确保所有16个舵机都有配置行
        for servo_id in range(16):
            if servo_id not in servo_lines:
                # 添加缺少的舵机行
                new_line = f"舵机{servo_id} {mid_values[servo_id]}"
                servo_lines[servo_id] = new_line
        
        # 添加所有舵机行（按舵机ID排序）
        for servo_id in sorted(servo_lines.keys()):
            updated_lines.append(servo_lines[servo_id])
        
        # 添加延时命令行（如果存在）
        if delay_line:
            updated_lines.append(delay_line)
        
        # 保存更新后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in updated_lines:
                f.write(line + '\n')
        
        print(f"文件已保存: {file_path}")
        return True
    except Exception as e:
        print(f"更新文件 {file_path} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

# 更新所有表情脚本
def update_all_expression_scripts(scripts_dir, config_file_path):
    # 加载配置
    config = load_servo_config(config_file_path)
    mid_values = get_servo_mid_values(config)
    
    print("最新的舵机中间值:")
    for servo_id, mid_value in sorted(mid_values.items()):
        print(f"舵机{servo_id}: {mid_value}")
    
    # 获取所有表情脚本文件
    script_files = [f for f in os.listdir(scripts_dir) if f.endswith('.txt')]
    
    print(f"\n找到 {len(script_files)} 个表情脚本文件")
    
    # 更新每个文件
    updated_count = 0
    for file_name in script_files:
        file_path = os.path.join(scripts_dir, file_name)
        if update_expression_script(file_path, mid_values):
            print(f"已更新: {file_name}")
            updated_count += 1
        else:
            print(f"更新失败: {file_name}")
    
    print(f"\n更新完成! 成功更新 {updated_count} 个文件")

if __name__ == "__main__":
    # 配置文件路径
    config_file = "servo_config.json"
    
    # 表情脚本目录
    scripts_dir = "表情脚本"
    
    # 执行更新
    update_all_expression_scripts(scripts_dir, config_file)
