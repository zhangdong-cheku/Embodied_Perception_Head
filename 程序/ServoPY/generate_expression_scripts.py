# filename: generate_expression_scripts.py
# 用途：自动生成所有表情脚本文件

import os
import json

def create_script(filename, content):
    """创建脚本文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建: {filename}")

def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '表情脚本')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    print("=" * 50)
    print("开始生成表情脚本文件...")
    print("=" * 50)
    
    # 读取配置文件获取中间值
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'servo_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 获取中间值
    mid_values = {}
    for i in range(16):
        mid_key = f"servo_{i}_mid"
        if mid_key in config:
            mid_values[i] = config[mid_key]
            print(f"设置舵机{i}中间值: {config[mid_key]}")
        else:
            print(f"警告: 配置文件中没有找到 {mid_key}")
            mid_values[i] = 90  # 默认值
    
    # 调试输出中间值
    print("读取到的中间值:")
    for servo, value in mid_values.items():
        print(f"舵机{servo}: {value}")

    # ============ 1. 中性表情 ============
    neutral_lines = []
    neutral_lines.append("# ============ 中性表情 ============")
    neutral_lines.append("# 所有舵机在中间值位置")
    neutral_lines.append("# 这是所有表情的基准状态")
    neutral_lines.append("")
    neutral_lines.append(f"舵机0 {config['servo_0_mid']}")
    neutral_lines.append(f"舵机1 {config['servo_1_mid']}")
    neutral_lines.append(f"舵机2 {config['servo_2_mid']}")
    neutral_lines.append(f"舵机3 {config['servo_3_mid']}")
    neutral_lines.append(f"舵机4 {config['servo_4_mid']}")
    neutral_lines.append(f"舵机5 {config['servo_5_mid']}")
    neutral_lines.append(f"舵机6 {config['servo_6_mid']}")
    neutral_lines.append(f"舵机7 {config['servo_7_mid']}")
    neutral_lines.append(f"舵机8 {config['servo_8_mid']}")
    neutral_lines.append(f"舵机9 {config['servo_9_mid']}")
    neutral_lines.append(f"舵机10 {config['servo_10_mid']}")
    neutral_lines.append(f"舵机11 {config['servo_11_mid']}")
    neutral_lines.append(f"舵机12 {config['servo_12_mid']}")
    neutral_lines.append(f"舵机13 {config['servo_13_mid']}")
    neutral_lines.append(f"舵机14 {config['servo_14_mid']}")
    neutral_lines.append(f"舵机15 {config['servo_15_mid']}")
    neutral_lines.append("延时 1000")
    neutral_content = "\n".join(neutral_lines)
    
    create_script(os.path.join(out_dir, '01_中性表情.txt'), neutral_content)
    
    # ============ 2. 微笑表情 ============
    # 计算微笑表情的偏移量（基于中间值）
    smile_offsets = {
        0: -3,   # 右下颚微闭
        1: +3,   # 左下颚微开
        2: -9,   # 右上唇下降
        3: -10,  # 左上唇下降
        4: +11,  # 右下唇上扬
        5: -7,   # 左下唇下降
        6: -8,   # 右上眼睑微闭
        7: +4,   # 左上眼睑微开
        8: -7,   # 右下眼睑微闭
        9: +6,   # 左下眼睑微开
        10: 0,   # 眼球平视
        11: 0,   # 眼球居中
        12: +4,  # 右眉梢微抬
        13: +6,  # 右眉头微降
        14: -7,  # 左眉梢微降
        15: +5   # 左眉头微抬
    }
    
    # 使用列表构建微笑表情脚本内容
    smile_lines = []
    smile_lines.append("# ============ 微笑表情 ============")
    smile_lines.append("# 嘴角上扬，眼睛微眯")
    smile_lines.append("# 下颚微闭，眉毛自然放松")
    smile_lines.append("")
    smile_lines.append(f"舵机0 {mid_values[0] + smile_offsets[0]}  # 右下颚微闭")
    smile_lines.append(f"舵机1 {mid_values[1] + smile_offsets[1]}  # 左下颚微开")
    smile_lines.append(f"舵机2 {mid_values[2] + smile_offsets[2]}  # 右上唇下降")
    smile_lines.append(f"舵机3 {mid_values[3] + smile_offsets[3]}  # 左上唇下降")
    smile_lines.append(f"舵机4 {mid_values[4] + smile_offsets[4]}  # 右下唇上扬")
    smile_lines.append(f"舵机5 {mid_values[5] + smile_offsets[5]}  # 左下唇下降")
    smile_lines.append(f"舵机6 {mid_values[6] + smile_offsets[6]}  # 右上眼睑微闭")
    smile_lines.append(f"舵机7 {mid_values[7] + smile_offsets[7]}  # 左上眼睑微开")
    smile_lines.append(f"舵机8 {mid_values[8] + smile_offsets[8]}  # 右下眼睑微闭")
    smile_lines.append(f"舵机9 {mid_values[9] + smile_offsets[9]}  # 左下眼睑微开")
    smile_lines.append(f"舵机10 {mid_values[10] + smile_offsets[10]}  # 眼球平视")
    smile_lines.append(f"舵机11 {mid_values[11] + smile_offsets[11]}  # 眼球居中")
    smile_lines.append(f"舵机12 {mid_values[12] + smile_offsets[12]}  # 右眉梢微抬")
    smile_lines.append(f"舵机13 {mid_values[13] + smile_offsets[13]}  # 右眉头微降")
    smile_lines.append(f"舵机14 {mid_values[14] + smile_offsets[14]}  # 左眉梢微降")
    smile_lines.append(f"舵机15 {mid_values[15] + smile_offsets[15]}  # 左眉头微抬")
    smile_lines.append("延时 2000")
    smile_content = "\n".join(smile_lines)
    
    create_script(os.path.join(out_dir, '02_微笑表情.txt'), smile_content)
    
    # ============ 3. 惊讶表情 ============
    # 计算惊讶表情的偏移量（基于中间值）
    surprise_offsets = {
        0: -6,   # 下巴微开
        1: +6,   # 下巴更开
        2: -14,  # 右上唇收紧
        3: -15,  # 左上唇收紧
        4: +6,   # 右下唇微收
        5: -12,  # 左下唇微收
        6: +4,   # 右上眼睑大睁
        7: -15,  # 左上眼睑大睁
        8: +8,   # 右下眼睑下拉
        9: -9,   # 左下眼睑上提
        10: -8,  # 眼球向上看
        11: 0,   # 眼球居中
        12: +9,  # 右眉梢上扬
        13: -12, # 右眉头下降
        14: -20, # 左眉梢下降
        15: +14  # 左眉头上扬
    }
    
    surprise_content = """# ============ 惊讶表情 ============
# 眼睛睁大，眉毛上扬
# 嘴巴微张，眼球向上看

舵机0 {0}  # 下巴微开
舵机1 {1}  # 下巴更开
舵机2 {2}  # 右上唇收紧
舵机3 {3}  # 左上唇收紧
舵机4 {4}  # 右下唇微收
舵机5 {5}  # 左下唇微收
舵机6 {6}  # 右上眼睑大睁
舵机7 {7}  # 左上眼睑大睁
舵机8 {8}  # 右下眼睑下拉
舵机9 {9}  # 左下眼睑上提
舵机10 {10} # 眼球向上看
舵机11 {11} # 眼球居中
舵机12 {12} # 右眉梢上扬
舵机13 {13} # 右眉头下降
舵机14 {14} # 左眉梢下降
舵机15 {15} # 左眉头上扬
延时 2000"""
    
    surprise_content = surprise_content.format(
        mid_values[0] + surprise_offsets[0],
        mid_values[1] + surprise_offsets[1],
        mid_values[2] + surprise_offsets[2],
        mid_values[3] + surprise_offsets[3],
        mid_values[4] + surprise_offsets[4],
        mid_values[5] + surprise_offsets[5],
        mid_values[6] + surprise_offsets[6],
        mid_values[7] + surprise_offsets[7],
        mid_values[8] + surprise_offsets[8],
        mid_values[9] + surprise_offsets[9],
        mid_values[10] + surprise_offsets[10],
        mid_values[11] + surprise_offsets[11],
        mid_values[12] + surprise_offsets[12],
        mid_values[13] + surprise_offsets[13],
        mid_values[14] + surprise_offsets[14],
        mid_values[15] + surprise_offsets[15]
    )
    
    create_script(os.path.join(out_dir, '03_惊讶表情.txt'), surprise_content)
    
    # ============ 4. 悲伤表情 ============
    # 计算悲伤表情的偏移量（基于中间值）
    sad_offsets = {
        0: 0,    # 下巴闭合
        1: 0,    # 下巴闭合
        2: +6,   # 右上唇下垂
        3: +5,   # 左上唇下垂
        4: -9,   # 右下唇下垂
        5: +8,   # 左下唇上提
        6: -13,  # 右上眼睑下垂
        7: +10,  # 左上眼睑下垂
        8: -12,  # 右下眼睑上提
        9: +6,   # 左下眼睑下垂
        10: +12, # 眼球向下看
        11: 0,   # 眼球居中
        12: -6,  # 右眉梢下垂
        13: +8,  # 右眉头上扬
        14: -1,  # 左眉梢上扬
        15: -6   # 左眉头下垂
    }
    
    sad_content = """# ============ 悲伤表情 ============
# 嘴角下垂，眉毛八字
# 眼睛半闭，眼球向下看

舵机0 {0}  # 下巴闭合
舵机1 {1}  # 下巴闭合
舵机2 {2}  # 右上唇下垂
舵机3 {3}  # 左上唇下垂
舵机4 {4}  # 右下唇下垂
舵机5 {5}  # 左下唇上提
舵机6 {6}  # 右上眼睑下垂
舵机7 {7}  # 左上眼睑下垂
舵机8 {8}  # 右下眼睑上提
舵机9 {9}  # 左下眼睑下垂
舵机10 {10} # 眼球向下看
舵机11 {11} # 眼球居中
舵机12 {12} # 右眉梢下垂
舵机13 {13} # 右眉头上扬
舵机14 {14} # 左眉梢上扬
舵机15 {15} # 左眉头下垂
延时 2000"""
    
    sad_content = sad_content.format(
        mid_values[0] + sad_offsets[0],
        mid_values[1] + sad_offsets[1],
        mid_values[2] + sad_offsets[2],
        mid_values[3] + sad_offsets[3],
        mid_values[4] + sad_offsets[4],
        mid_values[5] + sad_offsets[5],
        mid_values[6] + sad_offsets[6],
        mid_values[7] + sad_offsets[7],
        mid_values[8] + sad_offsets[8],
        mid_values[9] + sad_offsets[9],
        mid_values[10] + sad_offsets[10],
        mid_values[11] + sad_offsets[11],
        mid_values[12] + sad_offsets[12],
        mid_values[13] + sad_offsets[13],
        mid_values[14] + sad_offsets[14],
        mid_values[15] + sad_offsets[15]
    )
    
    create_script(os.path.join(out_dir, '04_悲伤表情.txt'), sad_content)
    
    # ============ 5. 愤怒表情 ============
    # 计算愤怒表情的偏移量（基于中间值）
    angry_offsets = {
        0: +2,   # 下巴咬紧
        1: -2,   # 下巴咬紧
        2: +11,  # 右上唇收紧
        3: +10,  # 左上唇收紧
        4: +16,  # 右下唇收紧
        5: -17,  # 左下唇收紧
        6: -18,  # 右上眼睑眯起
        7: +16,  # 左上眼睑眯起
        8: -17,  # 右下眼睑上提
        9: -4,   # 左下眼睑上提
        10: +2,  # 眼球平视怒瞪
        11: 0,   # 眼球居中
        12: -11, # 右眉梢下压
        13: +8,  # 右眉头上扬
        14: -1,  # 左眉梢上扬
        15: -1   # 左眉头下压
    }
    
    angry_content = """# ============ 愤怒表情 ============
# 眉毛下压，眼睛眯起
# 嘴唇紧绷，下巴咬紧

舵机0 {0}  # 下巴咬紧
舵机1 {1}  # 下巴咬紧
舵机2 {2}  # 右上唇收紧
舵机3 {3}  # 左上唇收紧
舵机4 {4}  # 右下唇收紧
舵机5 {5}  # 左下唇收紧
舵机6 {6}  # 右上眼睑眯起
舵机7 {7}  # 左上眼睑眯起
舵机8 {8}  # 右下眼睑上提
舵机9 {9}  # 左下眼睑上提
舵机10 {10} # 眼球平视怒瞪
舵机11 {11} # 眼球居中
舵机12 {12} # 右眉梢下压
舵机13 {13} # 右眉头上扬
舵机14 {14} # 左眉梢上扬
舵机15 {15} # 左眉头下压
延时 2000"""
    
    angry_content = angry_content.format(
        mid_values[0] + angry_offsets[0],
        mid_values[1] + angry_offsets[1],
        mid_values[2] + angry_offsets[2],
        mid_values[3] + angry_offsets[3],
        mid_values[4] + angry_offsets[4],
        mid_values[5] + angry_offsets[5],
        mid_values[6] + angry_offsets[6],
        mid_values[7] + angry_offsets[7],
        mid_values[8] + angry_offsets[8],
        mid_values[9] + angry_offsets[9],
        mid_values[10] + angry_offsets[10],
        mid_values[11] + angry_offsets[11],
        mid_values[12] + angry_offsets[12],
        mid_values[13] + angry_offsets[13],
        mid_values[14] + angry_offsets[14],
        mid_values[15] + angry_offsets[15]
    )
    
    create_script(os.path.join(out_dir, '05_愤怒表情.txt'), angry_content)
    
    # ============ 6. 眨眼动画 ============
    # 计算眨眼动画的偏移量（基于中间值）
    blink_offsets = {
        "initial": {
            6: 0,   # 右上眼睑 - 自然睁开
            7: 0,   # 左上眼睑 - 自然睁开
            8: 0,   # 右下眼睑 - 自然睁开
            9: 0    # 左下眼睑 - 自然睁开
        },
        "quick_close": {
            6: -8,  # 右上眼睑 - 快速闭合
            7: +9,  # 左上眼睑 - 快速闭合
            8: -7,  # 右下眼睑 - 快速上提
            9: +6   # 左下眼睑 - 快速上提
        },
        "full_close": {
            6: -13, # 右上眼睑 - 完全闭合
            7: +14, # 左上眼睑 - 完全闭合
            8: -12, # 右下眼睑 - 更上提
            9: +11  # 左下眼睑 - 更上提
        }
    }
    
    blink_content = """# ============ 眨眼动画 ============
# 自然快速的眨眼动作
# 所有角度在安全范围内

# 初始睁眼状态
舵机6 {servo6_initial}   # 右上眼睑
舵机7 {servo7_initial}   # 左上眼睑
舵机8 {servo8_initial}   # 右下眼睑
舵机9 {servo9_initial}   # 左下眼睑
延时 300

# 快速闭合
舵机6 {servo6_quick_close}   # 右上眼睑闭合
舵机7 {servo7_quick_close}   # 左上眼睑闭合
舵机8 {servo8_quick_close}   # 右下眼睑上提
舵机9 {servo9_quick_close}   # 左下眼睑上提
延时 80

# 完全闭合
舵机6 {servo6_full_close}   # 右上眼睑更闭
舵机7 {servo7_full_close}   # 左上眼睑更闭
舵机8 {servo8_full_close}   # 右下眼睑更上提
舵机9 {servo9_full_close}   # 左下眼睑更上提
延时 60

# 快速睁开
舵机6 {servo6_initial}   # 恢复睁开
舵机7 {servo7_initial}   # 恢复睁开
舵机8 {servo8_initial}   # 恢复
舵机9 {servo9_initial}   # 恢复
延时 500"""
    
    blink_content = blink_content.format(
        # 初始状态
        servo6_initial=mid_values[6] + blink_offsets["initial"][6],
        servo7_initial=mid_values[7] + blink_offsets["initial"][7],
        servo8_initial=mid_values[8] + blink_offsets["initial"][8],
        servo9_initial=mid_values[9] + blink_offsets["initial"][9],
        
        # 快速闭合状态
        servo6_quick_close=mid_values[6] + blink_offsets["quick_close"][6],
        servo7_quick_close=mid_values[7] + blink_offsets["quick_close"][7],
        servo8_quick_close=mid_values[8] + blink_offsets["quick_close"][8],
        servo9_quick_close=mid_values[9] + blink_offsets["quick_close"][9],
        
        # 完全闭合状态
        servo6_full_close=mid_values[6] + blink_offsets["full_close"][6],
        servo7_full_close=mid_values[7] + blink_offsets["full_close"][7],
        servo8_full_close=mid_values[8] + blink_offsets["full_close"][8],
        servo9_full_close=mid_values[9] + blink_offsets["full_close"][9]
    )
    
    create_script(os.path.join(out_dir, '06_眨眼动画.txt'), blink_content)
    
    # ============ 7. 完整表情演示 ============
    # 使用已定义的偏移量生成完整表情演示
    demo_content = """# ============ 完整表情演示 ============
# 自动演示所有基础表情
# 每个表情之间会回到中性状态

# 1. 中性表情（基准）
舵机0 {servo0_neutral}
舵机1 {servo1_neutral}
舵机2 {servo2_neutral}
舵机3 {servo3_neutral}
舵机4 {servo4_neutral}
舵机5 {servo5_neutral}
舵机6 {servo6_neutral}
舵机7 {servo7_neutral}
舵机8 {servo8_neutral}
舵机9 {servo9_neutral}
舵机10 {servo10_neutral}
舵机11 {servo11_neutral}
舵机12 {servo12_neutral}
舵机13 {servo13_neutral}
舵机14 {servo14_neutral}
舵机15 {servo15_neutral}
延时 1000

# 2. 微笑表情
舵机0 {servo0_smile}
舵机1 {servo1_smile}
舵机2 {servo2_smile}
舵机3 {servo3_smile}
舵机4 {servo4_smile}
舵机5 {servo5_smile}
舵机6 {servo6_smile}
舵机7 {servo7_smile}
舵机8 {servo8_smile}
舵机9 {servo9_smile}
舵机10 {servo10_smile}
舵机11 {servo11_smile}
舵机12 {servo12_smile}
舵机13 {servo13_smile}
舵机14 {servo14_smile}
舵机15 {servo15_smile}
延时 2000

# 回到中性
舵机0 {servo0_neutral}
舵机1 {servo1_neutral}
舵机2 {servo2_neutral}
舵机3 {servo3_neutral}
舵机4 {servo4_neutral}
舵机5 {servo5_neutral}
舵机6 {servo6_neutral}
舵机7 {servo7_neutral}
舵机8 {servo8_neutral}
舵机9 {servo9_neutral}
舵机10 {servo10_neutral}
舵机11 {servo11_neutral}
舵机12 {servo12_neutral}
舵机13 {servo13_neutral}
舵机14 {servo14_neutral}
舵机15 {servo15_neutral}
延时 1000

# 3. 惊讶表情
舵机0 {servo0_surprise}
舵机1 {servo1_surprise}
舵机2 {servo2_surprise}
舵机3 {servo3_surprise}
舵机4 {servo4_surprise}
舵机5 {servo5_surprise}
舵机6 {servo6_surprise}
舵机7 {servo7_surprise}
舵机8 {servo8_surprise}
舵机9 {servo9_surprise}
舵机10 {servo10_surprise}
舵机11 {servo11_surprise}
舵机12 {servo12_surprise}
舵机13 {servo13_surprise}
舵机14 {servo14_surprise}
舵机15 {servo15_surprise}
延时 2000

# 回到中性
舵机0 {servo0_neutral}
舵机1 {servo1_neutral}
舵机2 {servo2_neutral}
舵机3 {servo3_neutral}
舵机4 {servo4_neutral}
舵机5 {servo5_neutral}
舵机6 {servo6_neutral}
舵机7 {servo7_neutral}
舵机8 {servo8_neutral}
舵机9 {servo9_neutral}
舵机10 {servo10_neutral}
舵机11 {servo11_neutral}
舵机12 {servo12_neutral}
舵机13 {servo13_neutral}
舵机14 {servo14_neutral}
舵机15 {servo15_neutral}
延时 1000

# 4. 悲伤表情
舵机0 {servo0_sad}
舵机1 {servo1_sad}
舵机2 {servo2_sad}
舵机3 {servo3_sad}
舵机4 {servo4_sad}
舵机5 {servo5_sad}
舵机6 {servo6_sad}
舵机7 {servo7_sad}
舵机8 {servo8_sad}
舵机9 {servo9_sad}
舵机10 {servo10_sad}
舵机11 {servo11_sad}
舵机12 {servo12_sad}
舵机13 {servo13_sad}
舵机14 {servo14_sad}
舵机15 {servo15_sad}
延时 2000

# 回到中性
舵机0 {servo0_neutral}
舵机1 {servo1_neutral}
舵机2 {servo2_neutral}
舵机3 {servo3_neutral}
舵机4 {servo4_neutral}
舵机5 {servo5_neutral}
舵机6 {servo6_neutral}
舵机7 {servo7_neutral}
舵机8 {servo8_neutral}
舵机9 {servo9_neutral}
舵机10 {servo10_neutral}
舵机11 {servo11_neutral}
舵机12 {servo12_neutral}
舵机13 {servo13_neutral}
舵机14 {servo14_neutral}
舵机15 {servo15_neutral}
延时 1000

# 5. 愤怒表情
舵机0 {servo0_angry}
舵机1 {servo1_angry}
舵机2 {servo2_angry}
舵机3 {servo3_angry}
舵机4 {servo4_angry}
舵机5 {servo5_angry}
舵机6 {servo6_angry}
舵机7 {servo7_angry}
舵机8 {servo8_angry}
舵机9 {servo9_angry}
舵机10 {servo10_angry}
舵机11 {servo11_angry}
舵机12 {servo12_angry}
舵机13 {servo13_angry}
舵机14 {servo14_angry}
舵机15 {servo15_angry}
延时 2000

# 最后回到中性
舵机0 {servo0_neutral}
舵机1 {servo1_neutral}
舵机2 {servo2_neutral}
舵机3 {servo3_neutral}
舵机4 {servo4_neutral}
舵机5 {servo5_neutral}
舵机6 {servo6_neutral}
舵机7 {servo7_neutral}
舵机8 {servo8_neutral}
舵机9 {servo9_neutral}
舵机10 {servo10_neutral}
舵机11 {servo11_neutral}
舵机12 {servo12_neutral}
舵机13 {servo13_neutral}
舵机14 {servo14_neutral}
舵机15 {servo15_neutral}
延时 1000"""
    
    demo_content = demo_content.format(
        # 中性表情
        servo0_neutral=mid_values[0],
        servo1_neutral=mid_values[1],
        servo2_neutral=mid_values[2],
        servo3_neutral=mid_values[3],
        servo4_neutral=mid_values[4],
        servo5_neutral=mid_values[5],
        servo6_neutral=mid_values[6],
        servo7_neutral=mid_values[7],
        servo8_neutral=mid_values[8],
        servo9_neutral=mid_values[9],
        servo10_neutral=mid_values[10],
        servo11_neutral=mid_values[11],
        servo12_neutral=mid_values[12],
        servo13_neutral=mid_values[13],
        servo14_neutral=mid_values[14],
        servo15_neutral=mid_values[15],
        
        # 微笑表情
        servo0_smile=mid_values[0] + smile_offsets[0],
        servo1_smile=mid_values[1] + smile_offsets[1],
        servo2_smile=mid_values[2] + smile_offsets[2],
        servo3_smile=mid_values[3] + smile_offsets[3],
        servo4_smile=mid_values[4] + smile_offsets[4],
        servo5_smile=mid_values[5] + smile_offsets[5],
        servo6_smile=mid_values[6] + smile_offsets[6],
        servo7_smile=mid_values[7] + smile_offsets[7],
        servo8_smile=mid_values[8] + smile_offsets[8],
        servo9_smile=mid_values[9] + smile_offsets[9],
        servo10_smile=mid_values[10] + smile_offsets[10],
        servo11_smile=mid_values[11] + smile_offsets[11],
        servo12_smile=mid_values[12] + smile_offsets[12],
        servo13_smile=mid_values[13] + smile_offsets[13],
        servo14_smile=mid_values[14] + smile_offsets[14],
        servo15_smile=mid_values[15] + smile_offsets[15],
        
        # 惊讶表情
        servo0_surprise=mid_values[0] + surprise_offsets[0],
        servo1_surprise=mid_values[1] + surprise_offsets[1],
        servo2_surprise=mid_values[2] + surprise_offsets[2],
        servo3_surprise=mid_values[3] + surprise_offsets[3],
        servo4_surprise=mid_values[4] + surprise_offsets[4],
        servo5_surprise=mid_values[5] + surprise_offsets[5],
        servo6_surprise=mid_values[6] + surprise_offsets[6],
        servo7_surprise=mid_values[7] + surprise_offsets[7],
        servo8_surprise=mid_values[8] + surprise_offsets[8],
        servo9_surprise=mid_values[9] + surprise_offsets[9],
        servo10_surprise=mid_values[10] + surprise_offsets[10],
        servo11_surprise=mid_values[11] + surprise_offsets[11],
        servo12_surprise=mid_values[12] + surprise_offsets[12],
        servo13_surprise=mid_values[13] + surprise_offsets[13],
        servo14_surprise=mid_values[14] + surprise_offsets[14],
        servo15_surprise=mid_values[15] + surprise_offsets[15],
        
        # 悲伤表情
        servo0_sad=mid_values[0] + sad_offsets[0],
        servo1_sad=mid_values[1] + sad_offsets[1],
        servo2_sad=mid_values[2] + sad_offsets[2],
        servo3_sad=mid_values[3] + sad_offsets[3],
        servo4_sad=mid_values[4] + sad_offsets[4],
        servo5_sad=mid_values[5] + sad_offsets[5],
        servo6_sad=mid_values[6] + sad_offsets[6],
        servo7_sad=mid_values[7] + sad_offsets[7],
        servo8_sad=mid_values[8] + sad_offsets[8],
        servo9_sad=mid_values[9] + sad_offsets[9],
        servo10_sad=mid_values[10] + sad_offsets[10],
        servo11_sad=mid_values[11] + sad_offsets[11],
        servo12_sad=mid_values[12] + sad_offsets[12],
        servo13_sad=mid_values[13] + sad_offsets[13],
        servo14_sad=mid_values[14] + sad_offsets[14],
        servo15_sad=mid_values[15] + sad_offsets[15],
        
        # 愤怒表情
        servo0_angry=mid_values[0] + angry_offsets[0],
        servo1_angry=mid_values[1] + angry_offsets[1],
        servo2_angry=mid_values[2] + angry_offsets[2],
        servo3_angry=mid_values[3] + angry_offsets[3],
        servo4_angry=mid_values[4] + angry_offsets[4],
        servo5_angry=mid_values[5] + angry_offsets[5],
        servo6_angry=mid_values[6] + angry_offsets[6],
        servo7_angry=mid_values[7] + angry_offsets[7],
        servo8_angry=mid_values[8] + angry_offsets[8],
        servo9_angry=mid_values[9] + angry_offsets[9],
        servo10_angry=mid_values[10] + angry_offsets[10],
        servo11_angry=mid_values[11] + angry_offsets[11],
        servo12_angry=mid_values[12] + angry_offsets[12],
        servo13_angry=mid_values[13] + angry_offsets[13],
        servo14_angry=mid_values[14] + angry_offsets[14],
        servo15_angry=mid_values[15] + angry_offsets[15]
    )
    
    create_script(os.path.join(out_dir, '07_完整表情演示.txt'), demo_content)
    
    # ============ 8. 眼球运动演示 ============
    eye_movement_content = """# ============ 眼球运动演示 ============
# 眼球上下左右安全运动
# 眼球上下：71-113°，眼球左右：52-109°

# 初始正视前方
舵机10 83  # 眼球上下中间
舵机11 75  # 眼球左右中间
延时 500

# 看向左上
舵机10 75  # 向上
舵机11 65  # 向左
延时 500

# 看向右上
舵机10 75  # 向上
舵机11 85  # 向右
延时 500

# 看向左下
舵机10 95  # 向下
舵机11 65  # 向左
延时 500

# 看向右下
舵机10 95  # 向下
舵机11 85  # 向右
延时 500

# 水平扫视
舵机10 83  # 上下居中
舵机11 65  # 看左
延时 300
舵机11 85  # 看右
延时 300
舵机11 75  # 回中
延时 500

# 垂直运动
舵机11 75  # 左右居中
舵机10 75  # 向上
延时 300
舵机10 95  # 向下
延时 300
舵机10 83  # 回中
延时 500"""
    
    create_script(os.path.join(out_dir, '08_眼球运动演示.txt'), eye_movement_content)
    
    # ============ 9. 眉毛表情演示 ============
    eyebrow_content = """# ============ 眉毛表情演示 ============
# 眉毛的各种安全表情
# 右眉外：66-103°，右眉内：35-89°
# 左眉外：68-112°，左眉内：106-136°

# 中性眉毛
舵机12 86
舵机13 59
舵机14 87
舵机15 90
延时 500

# 挑眉（右眉上扬）
舵机12 95  # 右眉梢上扬
舵机13 50  # 右眉头下降
舵机14 87  # 左眉保持
舵机15 90  # 左眉保持
延时 1000

# 挑眉（左眉上扬）
舵机12 86  # 右眉恢复
舵机13 59  # 右眉恢复
舵机14 75  # 左眉梢下降
舵机15 105 # 左眉头上扬
延时 1000

# 皱眉（双眉内聚）
舵机12 80  # 右眉梢下降
舵机13 70  # 右眉头上扬
舵机14 95  # 左眉梢上扬
舵机15 85  # 左眉头下降
延时 1000

# 惊讶眉（双眉上扬）
舵机12 95  # 右眉梢上扬
舵机13 50  # 右眉头下降
舵机14 75  # 左眉梢下降
舵机15 105 # 左眉头上扬
延时 1000

# 悲伤眉（八字眉）
舵机12 80  # 右眉梢下垂
舵机13 70  # 右眉头上扬
舵机14 95  # 左眉梢上扬
舵机15 85  # 左眉头下垂
延时 1000

# 恢复中性
舵机12 86
舵机13 59
舵机14 87
舵机15 90
延时 500"""
    
    create_script(os.path.join(out_dir, '09_眉毛表情演示.txt'), eyebrow_content)
    
    # ============ 10. 说话口型演示 ============
    mouth_content = """# ============ 说话口型演示 ============
# 模拟说话时的口型变化
# 注意：所有角度在安全范围内

# 初始闭合状态
舵机0 108  # 右下颚闭合
舵机1 109  # 左下颚闭合
舵机2 79   # 右上唇自然
舵机3 55   # 左上唇自然
舵机4 109  # 右下唇自然
舵机5 62   # 左下唇自然
延时 300

# 发"啊"音（张开）
舵机0 102  # 下巴张开
舵机1 115  # 下巴张开
舵机2 70   # 上唇微提
舵机3 50   # 上唇微提
舵机4 115  # 下唇微降
舵机5 55   # 下唇微降
延时 200

# 发"呜"音（嘟嘴）
舵机0 108  # 下巴闭合
舵机1 109  # 下巴闭合
舵机2 85   # 上唇前突
舵机3 60   # 上唇前突
舵机4 100  # 下唇前突
舵机5 70   # 下唇前突
延时 200

# 发"咿"音（咧嘴）
舵机0 107  # 下巴微开
舵机1 110  # 下巴微开
舵机2 65   # 嘴角后拉
舵机3 45   # 嘴角后拉
舵机4 120  # 嘴角后拉
舵机5 50   # 嘴角后拉
延时 200

# 发"喔"音（圆唇）
舵机0 105  # 下巴张开
舵机1 112  # 下巴张开
舵机2 80   # 嘴唇收圆
舵机3 58   # 嘴唇收圆
舵机4 110  # 嘴唇收圆
舵机5 65   # 嘴唇收圆
延时 200

# 回到闭合状态
舵机0 108
舵机1 109
舵机2 79
舵机3 55
舵机4 109
舵机5 62
延时 300"""
    
    create_script(os.path.join(out_dir, '10_说话口型演示.txt'), mouth_content)
    
    print("\n" + "=" * 50)
    print("脚本生成完成！")
    print(f"共生成10个表情脚本文件")
    print(f"保存在: {out_dir}")
    print("=" * 50)
    
    # 显示文件列表
    print("\n📁 生成的文件列表:")
    files = os.listdir(out_dir)
    for i, filename in enumerate(sorted(files), 1):
        print(f"  {i:2d}. {filename}")
    
    print("\n💡 使用说明:")
    print("  1. 将脚本文件复制到ZS_BOX.py的脚本编辑区")
    print("  2. 点击'运行脚本'测试效果")
    print("  3. 根据实际效果微调角度")

if __name__ == "__main__":
    main()