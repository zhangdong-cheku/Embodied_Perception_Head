import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import json
import os
import re
from datetime import datetime

class ServoControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("仿生人头控制系统 - 增强版")
        
        # 串口相关
        self.serial_port = None
        self.is_connected = False
        
        # 舵机角度存储
        self.servo_angles = [90] * 16
        
        # 脚本文件路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_file = os.path.join(base_dir, "servo_scripts.json")
        self.current_script_name = ""
        self.scripts = self.load_scripts()
        
        # 舵机配置文件
        self.config_file = os.path.join(base_dir, "servo_config.json")
        self.servo_config = self.load_config()
        
        # 从配置文件加载初始角度到servo_angles数组
        for i in range(16):
            # 优先使用旧配置键（保持向后兼容）
            if f'servo_{i}_init' in self.servo_config:
                self.servo_angles[i] = self.servo_config[f'servo_{i}_init']
            elif f'servo_{i}_mid' in self.servo_config:
                self.servo_angles[i] = self.servo_config[f'servo_{i}_mid']
        
        # 保存初始安全边际
        self.jaw_safety_margin = 2
        
        # 创建界面
        self.create_widgets()
        
        # 根据加载的配置更新所有滑条范围
        self.update_servo_scales()
        
        # 自动刷新串口列表
        self.refresh_ports()
        
        # 添加窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.jaw_send_after_id = None
        self._pending_jaw_angle = None
        self.batch_supported = None
        self.suppress_send = False
        self.jaw_safety_margin = 2
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置主框架的权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 串口连接部分
        connection_frame = ttk.LabelFrame(main_frame, text="串口连接", padding="5")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 串口标签和选择框
        ttk.Label(connection_frame, text="串口:", font=('Arial', 11)).grid(row=0, column=0, padx=2, pady=3)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(connection_frame, textvariable=self.port_var, width=15, font=('Arial', 10))
        self.port_combo.grid(row=0, column=1, padx=2, pady=3)
        
        ttk.Label(connection_frame, text="波特率:", font=('Arial', 11)).grid(row=0, column=2, padx=2, pady=3)
        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(connection_frame, textvariable=self.baud_var, 
                                  values=["9600", "115200", "57600", "38400"], width=10, font=('Arial', 10))
        baud_combo.grid(row=0, column=3, padx=2, pady=3)
        
        # 连接按钮
        self.connect_btn = ttk.Button(connection_frame, text="连接", command=self.toggle_connection, width=7)
        self.connect_btn.grid(row=0, column=4, padx=3, pady=3)
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(connection_frame, text="刷新", command=self.refresh_ports, width=7)
        self.refresh_btn.grid(row=0, column=5, padx=3, pady=3)
        
        # 状态标签
        self.status_label = ttk.Label(connection_frame, text="未连接", foreground="red", font=('Arial', 11))
        self.status_label.grid(row=0, column=6, padx=5, pady=3)
        
        # 测试按钮
        self.test_btn = ttk.Button(connection_frame, text="测试通信", command=self.test_communication, width=9)
        self.test_btn.grid(row=0, column=7, padx=3, pady=3)
        
        # 自动发送角度复选框
        self.auto_send_var = tk.BooleanVar(value=self.servo_config.get('auto_send_angles', False))
        self.auto_send_check = ttk.Checkbutton(connection_frame, text="连接后自动发送角度", variable=self.auto_send_var, 
                                             command=self.toggle_auto_send_angles)
        self.auto_send_check.grid(row=0, column=8, padx=3, pady=3)
        
        # 初始化按钮 - 用于将所有舵机移动到中间位置
        self.init_btn = ttk.Button(connection_frame, text="初始化", command=self.initialize_servos, width=7)
        self.init_btn.grid(row=0, column=9, padx=3, pady=3)
        

        
        # 舵机控制部分
        servo_frame = ttk.LabelFrame(main_frame, text="舵机控制 (0-15)", padding="10")
        servo_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 设置舵机框架居中
        for i in range(5):
            servo_frame.grid_columnconfigure(i, weight=1)
        
        self.servo_controls = []
        
        # 1. 下颚舵机控制（舵机0和舵机1）
        jaw_frame = ttk.Frame(servo_frame)
        jaw_frame.grid(row=0, column=0, padx=8, pady=6, sticky=(tk.W, tk.E))
        
        # 下颚舵机标签
        ttk.Label(jaw_frame, text="下颚舵机 (0-1同步反向控制)", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky=tk.W, columnspan=4)
        
        # 角度滑块
        # 使用配置中的范围
        jaw_min = self.servo_config.get('servo_0_min', 0)
        jaw_max = self.servo_config.get('servo_0_max', 180)
        jaw_mid_angle = self.servo_config.get('servo_0_mid', 90)
        self.jaw_angle_var = tk.IntVar(value=jaw_mid_angle)
        self.jaw_scale = ttk.Scale(jaw_frame, from_=jaw_min, to=jaw_max, orient=tk.HORIZONTAL,
                            variable=self.jaw_angle_var, length=180,
                            command=lambda v: self.on_jaw_servo_change(v))
        
        # 放置滑条，与其他舵机布局一致
        self.jaw_scale.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # 创建角度显示标签，放在滑条后面（row=1, column=4），与其他舵机一致
        self.jaw_label = ttk.Label(jaw_frame, text=f"{jaw_mid_angle}°", width=4, font=("Arial", 11))
        self.jaw_label.grid(row=1, column=4, padx=5)
        
        # 最小角度配置
        ttk.Label(jaw_frame, text="最小角度:", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W)
        jaw_init_var = tk.StringVar(value=str(self.servo_config.get('servo_0_min', self.servo_config.get('servo_0_init', 90))))
        jaw_init_entry = ttk.Entry(jaw_frame, textvariable=jaw_init_var, width=6, font=("Arial", 11))
        jaw_init_entry.grid(row=2, column=1, padx=2)
        
        jaw_init_btn = ttk.Button(jaw_frame, text="执行", width=5,
                                command=lambda: self.set_servo_min(0))
        jaw_init_btn.grid(row=2, column=2, padx=2)
        
        # 最大角度配置
        ttk.Label(jaw_frame, text="最大角度:", font=("Arial", 11)).grid(row=3, column=0, sticky=tk.W)
        jaw_end_var = tk.StringVar(value=str(self.servo_config.get('servo_0_max', self.servo_config.get('servo_0_end', 90))))
        jaw_end_entry = ttk.Entry(jaw_frame, textvariable=jaw_end_var, width=6, font=("Arial", 11))
        jaw_end_entry.grid(row=3, column=1, padx=2)
        
        jaw_end_btn = ttk.Button(jaw_frame, text="执行", width=5,
                               command=lambda: self.set_servo_max(0))
        jaw_end_btn.grid(row=3, column=2, padx=2)
        
        # 中间值配置
        ttk.Label(jaw_frame, text="中间值:", font=("Arial", 11)).grid(row=4, column=0, sticky=tk.W)
        jaw_mid_var = tk.StringVar(value=str(self.servo_config.get('servo_0_mid', 90)))
        jaw_mid_entry = ttk.Entry(jaw_frame, textvariable=jaw_mid_var, width=6, font=("Arial", 11))
        jaw_mid_entry.grid(row=4, column=1, padx=2)
        
        jaw_mid_btn = ttk.Button(jaw_frame, text="执行", width=5,
                               command=lambda: self.set_servo_mid(0))
        jaw_mid_btn.grid(row=4, column=2, padx=2)
        
        # 添加下颚舵机控件
        self.servo_controls.append({
            'var': self.jaw_angle_var,
            'scale': self.jaw_scale,
            'label': self.jaw_label,
            'init_var': jaw_init_var,
            'end_var': jaw_end_var,
            'mid_var': jaw_mid_var
        })
        
        # 为舵机1添加一个空的控制项
        self.servo_controls.append({})
        
        # 2. 显示剩余的舵机（从2开始）
        servo_names = [
            "舵机2-右上唇", "舵机3-左上唇",
            "舵机4-右下唇", "舵机5-左下唇", "舵机6-右上眼睑", "舵机7-左上眼睑",
            "舵机8-右下眼睑", "舵机9-左下眼睑", "舵机10-左右眼球上下", "舵机11-左右眼球左右",
            "舵机12-右眉毛外", "舵机13-右眉毛内", "舵机14-左眉毛外", "舵机15-左眉毛内"
        ]
        
        for i in range(2, 16):
            row = (i - 2) // 5 + 1
            col = (i - 2) % 5
            
            frame = ttk.Frame(servo_frame)
            frame.grid(row=row, column=col, padx=8, pady=6, sticky=(tk.W, tk.E))
            
            # 舵机标签
            ttk.Label(frame, text=servo_names[i-2], font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, columnspan=4)
            
            # 角度滑块
            mid_angle = self.servo_config.get(f'servo_{i}_mid', 90)
            angle_var = tk.IntVar(value=mid_angle)
            scale = ttk.Scale(frame, from_=0, to=180, orient=tk.HORIZONTAL, 
                            variable=angle_var, length=150,
                            command=lambda v, idx=i: self.on_servo_change(idx, v))
            scale.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
            
            angle_label = ttk.Label(frame, text=f"{mid_angle}°", width=4, font=("Arial", 10))
            angle_label.grid(row=1, column=4, padx=5)
            
            # 最小角度配置
            ttk.Label(frame, text="最小角度:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W)
            min_var = tk.StringVar(value=str(self.servo_config.get(f'servo_{i}_min', self.servo_config.get(f'servo_{i}_init', 90))))
            min_entry = ttk.Entry(frame, textvariable=min_var, width=6, font=("Arial", 10))
            min_entry.grid(row=2, column=1, padx=2)
            
            init_btn = ttk.Button(frame, text="执行", width=4,
                                command=lambda idx=i: self.set_servo_min(idx))
            init_btn.grid(row=2, column=2, padx=2)
            
            # 最大角度配置
            ttk.Label(frame, text="最大角度:", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W)
            max_var = tk.StringVar(value=str(self.servo_config.get(f'servo_{i}_max', self.servo_config.get(f'servo_{i}_end', 90))))
            max_entry = ttk.Entry(frame, textvariable=max_var, width=6, font=("Arial", 10))
            max_entry.grid(row=3, column=1, padx=2)
            
            end_btn = ttk.Button(frame, text="执行", width=4,
                               command=lambda idx=i: self.set_servo_max(idx))
            end_btn.grid(row=3, column=2, padx=2)
            
            # 中间值配置
            ttk.Label(frame, text="中间值:", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W)
            mid_var = tk.StringVar(value=str(self.servo_config.get(f'servo_{i}_mid', 90)))
            mid_entry = ttk.Entry(frame, textvariable=mid_var, width=6, font=("Arial", 10))
            mid_entry.grid(row=4, column=1, padx=2)
            
            mid_btn = ttk.Button(frame, text="执行", width=4,
                               command=lambda idx=i: self.set_servo_mid(idx))
            mid_btn.grid(row=4, column=2, padx=2)
            
            self.servo_controls.append({
                'var': angle_var,
                'scale': scale,
                'label': angle_label,
                'min_var': min_var,
                'max_var': max_var,
                'mid_var': mid_var
            })
        
        # 按钮区域
        buttons_frame = ttk.Frame(servo_frame)
        buttons_frame.grid(row=4, column=0, columnspan=5, pady=15, sticky=(tk.W, tk.E))
        
        # 设置列权重，使按钮均匀分布
        buttons_frame.grid_columnconfigure(0, weight=1, uniform="buttons")
        buttons_frame.grid_columnconfigure(1, weight=1, uniform="buttons")
        buttons_frame.grid_columnconfigure(2, weight=1, uniform="buttons")
        buttons_frame.grid_columnconfigure(3, weight=2, uniform="buttons")
        
        # 所有按钮，均匀分布
        save_all_btn = ttk.Button(buttons_frame, text="💾 保存所有配置", 
                                 command=self.save_all_config, width=14)
        save_all_btn.grid(row=0, column=0, padx=10, pady=8)
        
        reset_all_btn = ttk.Button(buttons_frame, text="🔄 回到中间值", 
                                  command=self.reset_all_servos, width=14)
        reset_all_btn.grid(row=0, column=1, padx=10, pady=8)
        
        reset_scales_btn = ttk.Button(buttons_frame, text="🔧 重新配置角度", 
                                     command=self.reset_servo_scales, width=14)
        reset_scales_btn.grid(row=0, column=2, padx=10, pady=8)
        
        # 单独配置舵机区域 - 更紧凑的布局
        single_config_frame = ttk.Frame(buttons_frame)
        single_config_frame.grid(row=0, column=3, padx=20, pady=8, sticky=tk.W)
        
        ttk.Label(single_config_frame, text="⚙️ 单独配置舵机:", font=(
            "Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=2)
        self.single_servo_var = tk.StringVar(value="0")
        single_servo_entry = ttk.Entry(single_config_frame, textvariable=self.single_servo_var, width=5, font=("Arial", 10))
        single_servo_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(single_config_frame, text="确定", 
                  command=self.configure_single_servo, width=8).grid(row=0, column=2, padx=5, pady=2)
        

        
        # 脚本编辑部分
        script_frame = ttk.LabelFrame(main_frame, text="脚本编辑", padding="10")
        script_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        main_frame.rowconfigure(2, weight=3)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 设置脚本框架的权重
        script_frame.rowconfigure(2, weight=1)
        script_frame.columnconfigure(0, weight=1)
        script_frame.columnconfigure(1, weight=1)
        
        # 脚本控制按钮
        script_btn_frame = ttk.Frame(script_frame)
        script_btn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 左侧脚本控制按钮
        left_script_btns = ttk.Frame(script_btn_frame)
        left_script_btns.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(left_script_btns, text="运行脚本", command=self.run_script, width=10).pack(side=tk.LEFT, padx=4)
        ttk.Button(left_script_btns, text="停止", command=self.stop_script, width=8).pack(side=tk.LEFT, padx=4)
        ttk.Button(left_script_btns, text="保存脚本", command=self.save_script, width=10).pack(side=tk.LEFT, padx=4)
        
        # 右侧脚本控制按钮
        right_script_btns = ttk.Frame(script_btn_frame)
        right_script_btns.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(right_script_btns, text="生成表情脚本", command=self.generate_expression_script, width=12).pack(side=tk.RIGHT, padx=4)
        ttk.Button(right_script_btns, text="插入示例", command=self.insert_example, width=10).pack(side=tk.RIGHT, padx=4)
        ttk.Button(right_script_btns, text="新建脚本", command=self.new_script, width=10).pack(side=tk.RIGHT, padx=4)
        ttk.Button(right_script_btns, text="加载脚本", command=self.load_script_dialog, width=10).pack(side=tk.RIGHT, padx=4)
        
        # 脚本名称
        ttk.Label(script_btn_frame, text="脚本名:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(20, 5))
        self.script_name_var = tk.StringVar(value="未命名")
        self.script_name_entry = ttk.Entry(script_btn_frame, textvariable=self.script_name_var, width=20, font=("Arial", 11))
        self.script_name_entry.pack(side=tk.LEFT, padx=5)
        
        # 脚本文本框
        ttk.Label(script_frame, text="脚本内容 (命令格式: '舵机X 角度' 或 '延时 毫秒数'):", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W)
        
        # 创建带行号的文本框框架
        script_text_frame = ttk.Frame(script_frame)
        script_text_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 行号文本框
        self.line_numbers = tk.Text(script_text_frame, width=5, height=12, font=("Arial", 11), 
                                   state=tk.DISABLED, bg="lightgray", relief=tk.FLAT)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 脚本内容文本框
        self.script_text = scrolledtext.ScrolledText(script_text_frame, height=15, font=("Arial", 11))
        self.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定文本变化事件以更新行号
        self.script_text.bind('<KeyRelease>', self.update_line_numbers)
        self.script_text.bind('<Button-1>', self.update_line_numbers)
        
        # 初始更新行号
        self.root.after(100, self.update_line_numbers)
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        main_frame.rowconfigure(3, weight=1)
        
        # 设置日志框架的权重
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # 增加日志输出内容栏
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Arial", 11))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 加载上次的脚本
        self.load_last_script()
        
        # 运行标志
        self.running_script = False
        self.script_thread = None
        
    def insert_example(self):
        """插入示例脚本"""
        example = """# 示例脚本 - 以#开头的行为注释
# 命令格式: 舵机X 角度 或 延时 毫秒数
# 延时单位为毫秒(ms), 1000ms = 1秒

# 舵机测试序列
舵机0 0
延时 500
舵机0 90
延时 500
舵机0 180
延时 1000

# 多个舵机同时动作
舵机1 30
舵机2 60
舵机3 90
延时 2000

# 复位所有测试的舵机
舵机0 90
舵机1 90
舵机2 90
舵机3 90
延时 1000

# 波浪动作示例
舵机0 45
延时 200
舵机1 45
延时 200
舵机2 45
延时 200
舵机3 45
延时 500

舵机0 135
延时 200
舵机1 135
延时 200
舵机2 135
延时 200
舵机3 135
延时 500

# 复位
舵机0 90
舵机1 90
舵机2 90
舵机3 90
"""
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert("1.0", example)
        self.update_line_numbers()
        
    def generate_expression_script(self):
        """生成表情脚本，确保所有舵机角度都在最小和最大范围内"""
        try:
            # 获取每个舵机的最小、最大和中间角度
            servo_params = {}
            for i in range(16):
                if i < len(self.servo_controls) and self.servo_controls[i]:
                    # 针对不同舵机使用不同的变量名
                    if i == 0:  # 下颚舵机
                        min_angle = int(self.servo_controls[i]['init_var'].get())
                        max_angle = int(self.servo_controls[i]['end_var'].get())
                        mid_angle = int(self.servo_controls[i]['mid_var'].get())
                    else:  # 其他舵机
                        min_angle = int(self.servo_controls[i]['min_var'].get())
                        max_angle = int(self.servo_controls[i]['max_var'].get())
                        mid_angle = int(self.servo_controls[i]['mid_var'].get())
                    servo_params[i] = {
                        'min': min_angle,
                        'max': max_angle,
                        'mid': mid_angle
                    }
            
            # 生成脚本内容
            script = """# 表情脚本 - 所有角度均在最小/最大范围内
# 命令格式: 舵机X 角度 或 延时 毫秒数
# 延时单位为毫秒(ms), 1000ms = 1秒

# 确保所有角度都在最小/最大范围内的函数
# 以下表情配置基于当前舵机的最小、最大和中间角度值

"""
            
            # 添加角度配置信息
            script += "# 当前舵机角度配置\n"
            for servo_id, params in sorted(servo_params.items()):
                script += f"# 舵机{servo_id}: 最小={params['min']}°, 中间={params['mid']}°, 最大={params['max']}°\n"
            script += "\n"
            
            # 生成表情序列
            def generate_angle(servo_id, ratio):
                """根据比例生成角度，确保在min和max之间"""
                if servo_id not in servo_params:
                    return 90  # 默认值
                params = servo_params[servo_id]
                range_angle = params['max'] - params['min']
                return int(params['min'] + range_angle * ratio)
            
            # 1. 初始状态（中间值）
            script += "# 1. 初始状态（中间值）\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1000\n\n"
            
            # 2. 微笑表情
            script += "# 2. 微笑表情\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    if servo_id == 0 or servo_id == 1:  # 下颚舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.3)}\n"  # 下巴向下
                    elif 2 <= servo_id <= 7:  # 眼部和眉毛舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.3)}\n"  # 眉毛上扬
                    else:  # 其他舵机
                        script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1500\n\n"
            
            # 3. 惊讶表情
            script += "# 3. 惊讶表情\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    if servo_id == 0 or servo_id == 1:  # 下颚舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.2)}\n"  # 下巴大幅度向下
                    elif 2 <= servo_id <= 7:  # 眼部和眉毛舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.2)}\n"  # 眉毛大幅度上扬
                    elif 8 <= servo_id <= 11:  # 眼睛周围舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.7)}\n"  # 眼睛睁大
                    else:  # 其他舵机
                        script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1500\n\n"
            
            # 4. 生气表情
            script += "# 4. 生气表情\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    if servo_id == 0 or servo_id == 1:  # 下颚舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.8)}\n"  # 下巴紧绷
                    elif 2 <= servo_id <= 7:  # 眼部和眉毛舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.7)}\n"  # 眉毛下压
                    elif 8 <= servo_id <= 11:  # 眼睛周围舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.3)}\n"  # 眼睛眯起
                    else:  # 其他舵机
                        script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1500\n\n"
            
            # 5. 悲伤表情
            script += "# 5. 悲伤表情\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    if servo_id == 0 or servo_id == 1:  # 下颚舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.6)}\n"  # 下巴微张
                    elif 2 <= servo_id <= 7:  # 眼部和眉毛舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.6)}\n"  # 眉毛内扣
                    elif 8 <= servo_id <= 11:  # 眼睛周围舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.5)}\n"  # 眼睛半闭
                    else:  # 其他舵机
                        script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1500\n\n"
            
            # 6. 思考表情
            script += "# 6. 思考表情\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    if servo_id == 0 or servo_id == 1:  # 下颚舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.5)}\n"  # 下巴微张
                    elif 2 <= servo_id <= 7:  # 眼部和眉毛舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.4)}\n"  # 眉毛一侧上扬
                    elif 8 <= servo_id <= 11:  # 眼睛周围舵机
                        script += f"舵机{servo_id} {generate_angle(servo_id, 0.6)}\n"  # 眼睛微眯
                    else:  # 其他舵机
                        script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1500\n\n"
            
            # 7. 回到初始状态
            script += "# 7. 回到初始状态\n"
            for servo_id in range(16):
                if servo_id in servo_params:
                    script += f"舵机{servo_id} {servo_params[servo_id]['mid']}\n"
            script += "延时 1000\n"
            
            # 插入到脚本编辑器
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", script)
            self.update_line_numbers()
            self.log("表情脚本生成成功，所有角度均在最小/最大范围内")
            
        except Exception as e:
            self.log(f"生成表情脚本失败: {e}", "ERROR")
        
    def update_line_numbers(self, event=None):
        """更新行号显示"""
        content = self.script_text.get("1.0", tk.END)
        lines = content.split('\n')
        num_lines = len(lines)
        
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        
        for i in range(1, num_lines + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")
        
        self.line_numbers.config(state=tk.DISABLED)
        
    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        
        # 尝试加载保存的串口号
        saved_port = self.servo_config.get('saved_port', '')
        if saved_port and saved_port in port_list:
            self.port_var.set(saved_port)
            self.log(f"已加载保存的串口: {saved_port}")
        elif port_list:
            self.port_combo.current(0)
        
        self.log("刷新串口列表完成")
        
    def toggle_connection(self):
        """切换串口连接状态"""
        if not self.is_connected:
            try:
                port = self.port_var.get()
                if not port:
                    messagebox.showerror("错误", "请选择串口")
                    return
                    
                baud = int(self.baud_var.get())
                
                # 连接串口
                self.serial_port = serial.Serial(port, baud, timeout=1)
                time.sleep(2)  # 等待Arduino重启
                
                # 验证连接
                if self.serial_port.is_open:
                    self.is_connected = True
                    self.connect_btn.config(text="断开")
                    self.status_label.config(text="已连接", foreground="green")
                    self.log(f"成功连接到 {port}")
                    
                    # 清空缓冲区
                    if self.serial_port.in_waiting:
                        self.serial_port.read(self.serial_port.in_waiting)
                    
                    # 保存串口号到配置
                    self.servo_config['saved_port'] = port
                    self.save_config()
                    
                    # 发送测试命令验证连接
                    self.log("发送测试命令验证连接...")
                    
                    # 增加重试机制，最多尝试3次
                    response_received = False
                    max_attempts = 3
                    for attempt in range(max_attempts):
                        # 清空缓冲区
                        if self.serial_port.in_waiting:
                            self.serial_port.read(self.serial_port.in_waiting)
                        
                        # 发送HELP命令
                        self.serial_port.write(b"HELP\n")
                        time.sleep(0.8)  # 增加等待时间
                        
                        if self.serial_port.in_waiting:
                            # 读取所有响应行
                            while self.serial_port.in_waiting:
                                response = self.serial_port.readline().decode().strip()
                                if response:  # 只记录非空响应
                                    self.log(f"ESP32响应: {response}")
                            response_received = True
                            break
                        else:
                            if attempt < max_attempts - 1:
                                self.log(f"重试测试命令... (尝试 {attempt + 2}/{max_attempts})")
                                time.sleep(1)
                    
                    if not response_received:
                        self.log("警告: 未收到ESP32初始响应")
                        self.log("建议: 检查ESP32电源、I2C连接或固件是否正常")
                    
                    # 检查是否需要在连接后自动发送存储的角度
                    auto_send_angles = self.servo_config.get('auto_send_angles', False)
                    if auto_send_angles:
                        # 连接建立后，发送当前存储的角度到所有舵机
                        self.log("连接建立后，发送当前存储的角度到所有舵机...")
                        # 先发送下颚舵机角度
                        if len(self.servo_angles) > 0:
                            self.send_jaw_servo_commands(self.servo_angles[0])
                            time.sleep(0.2)
                        # 再发送其他舵机角度
                        for i in range(2, 16):
                            if i < len(self.servo_angles):
                                self.send_servo_command(i, self.servo_angles[i])
                                time.sleep(0.1)
                    else:
                        self.log("连接建立后，不自动发送存储的角度（可在配置中修改此选项）")
                        
                else:
                    raise Exception("串口未成功打开")
                    
            except Exception as e:
                messagebox.showerror("连接错误", str(e))
                self.log(f"连接失败: {e}", "ERROR")
                if self.serial_port:
                    self.serial_port.close()
                self.serial_port = None
                self.is_connected = False
        else:
            try:
                if self.serial_port:
                    self.serial_port.close()
                self.is_connected = False
                self.connect_btn.config(text="连接")
                self.status_label.config(text="未连接", foreground="red")
                self.log("已断开连接")
                self.serial_port = None
            except Exception as e:
                self.log(f"断开连接失败: {e}", "ERROR")
                
    def test_communication(self):
        """测试通信"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return
            
        try:
            self.log("测试通信...")
            # 清空缓冲区
            if self.serial_port.in_waiting:
                self.serial_port.read(self.serial_port.in_waiting)
            
            # 发送状态查询命令
            self.serial_port.write(b"STATUS\n")
            time.sleep(0.5)
            
            if self.serial_port.in_waiting:
                response = self.serial_port.readline().decode().strip()
                self.log(f"测试响应: {response}")
                messagebox.showinfo("测试成功", "通信正常")
            else:
                self.log("未收到响应", "WARNING")
                messagebox.showwarning("测试失败", "未收到响应")
        except Exception as e:
            self.log(f"测试失败: {e}", "ERROR")
            messagebox.showerror("测试失败", str(e))
    

    
    def on_servo_change(self, servo_id, value):
        """舵机滑块变化时的回调，使用防抖机制减少命令发送频率"""
        try:
            angle = int(float(value))
            
            # 确保角度在配置的范围内
            servo_min = self.servo_config.get(f'servo_{servo_id}_min', 0)
            servo_max = self.servo_config.get(f'servo_{servo_id}_max', 180)
            if angle < servo_min:
                angle = servo_min
            elif angle > servo_max:
                angle = servo_max
            
            # 更新内部状态
            self.servo_angles[servo_id] = angle
            
            # 更新标签
            if servo_id < len(self.servo_controls) and 'label' in self.servo_controls[servo_id]:
                self.servo_controls[servo_id]['label'].config(text=f"{angle}°")
            
            # 发送命令（使用防抖机制）
            if self.is_connected and not self.suppress_send:
                # 设置防抖参数
                self._pending_servo_id = servo_id
                self._pending_servo_angle = angle
                
                # 取消之前的延迟命令
                if hasattr(self, '_servo_send_after_id') and self._servo_send_after_id is not None:
                    try:
                        self.root.after_cancel(self._servo_send_after_id)
                    except Exception:
                        pass
                
                # 设置新的延迟命令
                self._servo_send_after_id = self.root.after(40, self._send_servo_angle_debounced)
                    
        except Exception as e:
            self.log(f"舵机{servo_id}控制出错: {e}", "ERROR")
    
    def _send_servo_angle_debounced(self):
        """防抖后发送舵机命令的方法"""
        self._servo_send_after_id = None
        if not self.is_connected:
            return
        if not hasattr(self, '_pending_servo_id') or self._pending_servo_id is None:
            return
        if not hasattr(self, '_pending_servo_angle') or self._pending_servo_angle is None:
            return
        
        servo_id = self._pending_servo_id
        angle = self._pending_servo_angle
        
        # 确保角度在有效范围内
        servo_min = self.servo_config.get(f'servo_{servo_id}_min', 0)
        servo_max = self.servo_config.get(f'servo_{servo_id}_max', 180)
        angle = max(servo_min, min(servo_max, angle))
        
        try:
            if servo_id == 0 or servo_id == 1:
                self.send_jaw_servo_commands(angle, wait_response=False, verbose=False)
            else:
                self.send_servo_command(servo_id, angle, wait_response=False)
        except Exception as e:
            self.log(f"防抖发送舵机{servo_id}命令出错: {e}", "ERROR")
    
    def on_jaw_servo_change(self, value):
        try:
            angle = int(float(value))
            jaw_min = self.servo_config.get('servo_0_min', 0)
            jaw_max = self.servo_config.get('servo_0_max', 180)
            if angle < jaw_min:
                angle = jaw_min
            elif angle > jaw_max:
                angle = jaw_max
            
            # 更新内部状态，保持反向同步
            self.servo_angles[0] = angle
            self.servo_angles[1] = 180 - angle
            
            if hasattr(self, 'jaw_label'):
                self.jaw_label.config(text=f"{angle}°")
            self._pending_jaw_angle = angle
            if self.suppress_send:
                if self.jaw_send_after_id is not None:
                    try:
                        self.root.after_cancel(self.jaw_send_after_id)
                    except Exception:
                        pass
                return
            if self.jaw_send_after_id is not None:
                try:
                    self.root.after_cancel(self.jaw_send_after_id)
                except Exception:
                    pass
            self.jaw_send_after_id = self.root.after(60, self._send_jaw_angles_debounced)
        except Exception as e:
            self.log(f"下颚舵机控制出错: {e}", "ERROR")
    
    def send_jaw_servo_commands(self, angle, wait_response=False, verbose=False):
        """同时发送命令到两个下颚舵机（反向运动）"""
        try:
            if verbose:
                self.log(f"===== send_jaw_servo_commands 开始 =====")
                self.log(f"send_jaw_servo_commands 被调用，angle: {angle}")
            
            # 检查串口连接状态
            if verbose:
                self.log(f"检查串口连接状态: is_connected={self.is_connected}, serial_port={self.serial_port}")
            if not self.is_connected or not self.serial_port:
                if verbose:
                    self.log(f"串口未连接，无法发送命令", "WARNING")
                messagebox.showwarning("警告", "串口未连接，无法发送命令")
                return False
            
            # 获取舵机配置范围
            servo0_min = self.servo_config.get('servo_0_min', 0)
            servo0_max = self.servo_config.get('servo_0_max', 180)
            servo1_min = self.servo_config.get('servo_1_min', 0)
            servo1_max = self.servo_config.get('servo_1_max', 180)
            
            # 安全检查：确保最小和最大角度有合理的范围
            if servo0_min >= servo0_max or servo0_max - servo0_min < 5:
                # 如果范围太小或不合理，使用默认安全范围
                servo0_min = 0
                servo0_max = 180
            
            if servo1_min >= servo1_max or servo1_max - servo1_min < 5:
                # 如果范围太小或不合理，使用默认安全范围
                servo1_min = 0
                servo1_max = 180
            
            # 确保servo0_min <= servo0_max
            if servo0_min > servo0_max:
                servo0_min, servo0_max = servo0_max, servo0_min
            
            # 确保servo1_min <= servo1_max
            if servo1_min > servo1_max:
                servo1_min, servo1_max = servo1_max, servo1_min
            
            servo0_safe_min = servo0_min
            servo0_safe_max = servo0_max
            servo1_safe_min = servo1_min
            servo1_safe_max = servo1_max
            
            # 保持滑条范围始终为0-180°，提供更直观的用户体验
            slider_min = 0
            slider_max = 180
            if verbose:
                self.log(f"滑条范围: slider_min={slider_min}, slider_max={slider_max}")
                self.log(f"舵机0有效范围: servo0_min={servo0_min}, servo0_max={servo0_max}")
                self.log(f"舵机1有效范围: servo1_min={servo1_min}, servo1_max={servo1_max}")
                self.log(f"安全范围: servo0_safe_min={servo0_safe_min}, servo0_safe_max={servo0_safe_max}")
                self.log(f"安全范围: servo1_safe_min={servo1_safe_min}, servo1_safe_max={servo1_safe_max}")
            
            # 确保角度在滑条的整个范围内
            slider_angle = max(slider_min, min(slider_max, angle))
            slider_angle = int(slider_angle)
            if verbose:
                self.log(f"滑条角度(限制后): {slider_angle}")
            
            # 确保角度在滑条的整个范围内
            slider_angle = max(slider_min, min(slider_max, angle))
            slider_angle = int(slider_angle)
            
            # 将滑条角度映射到两个舵机的安全范围内，同时保持反向同步
            # 首先计算理想的舵机0角度
            ideal_servo0_angle = max(servo0_safe_min, min(servo0_safe_max, slider_angle))
            # 计算理想的舵机1角度，保持反向同步
            ideal_servo1_angle = 180 - ideal_servo0_angle
            
            # 检查理想的舵机1角度是否在安全范围内
            if ideal_servo1_angle < servo1_safe_min or ideal_servo1_angle > servo1_safe_max:
                # 如果不在范围内，调整舵机1角度到安全边界
                if ideal_servo1_angle < servo1_safe_min:
                    servo1_angle = servo1_safe_min
                else:
                    servo1_angle = servo1_safe_max
                # 重新计算舵机0角度以保持反向同步
                servo0_angle = 180 - servo1_angle
                
                # 再次检查舵机0角度是否在安全范围内
                if servo0_angle < servo0_safe_min or servo0_angle > servo0_safe_max:
                    # 如果不在范围内，需要调整到安全边界
                    if servo0_angle < servo0_safe_min:
                        servo0_angle = servo0_safe_min
                        servo1_angle = 180 - servo0_angle
                    else:
                        servo0_angle = servo0_safe_max
                        servo1_angle = 180 - servo0_angle
                    
                    # 最后确保舵机1角度也在安全范围内
                    servo1_angle = max(servo1_safe_min, min(servo1_safe_max, servo1_angle))
                    servo0_angle = 180 - servo1_angle
            else:
                # 如果理想角度都在安全范围内，直接使用
                servo0_angle = ideal_servo0_angle
                servo1_angle = ideal_servo1_angle
            
            # 确保最终角度都在安全范围内
            servo0_angle = max(servo0_safe_min, min(servo0_safe_max, int(servo0_angle)))
            servo1_angle = max(servo1_safe_min, min(servo1_safe_max, int(servo1_angle)))
            
            # 强制保持反向同步
            if abs(servo0_angle + servo1_angle - 180) > 1:
                servo1_angle = 180 - servo0_angle
                # 再次确保舵机1角度在安全范围内
                servo1_angle = max(servo1_safe_min, min(servo1_safe_max, int(servo1_angle)))
                # 如果调整了舵机1角度，再次调整舵机0角度
                servo0_angle = 180 - servo1_angle
                servo0_angle = max(servo0_safe_min, min(servo0_safe_max, int(servo0_angle)))
                
                # 再次确保在安全范围内
                servo0_angle = max(servo0_safe_min, min(servo0_safe_max, servo0_angle))
                servo1_angle = max(servo1_safe_min, min(servo1_safe_max, servo1_angle))
            

            
            if verbose:
                self.log(f"计算后的servo0_angle: {servo0_angle}")
                self.log(f"计算后的servo1_angle: {servo1_angle}")
            
            # 最后确保角度在安全范围内
            if not wait_response:
                # 交互场景加入安全余量
                servo0_angle = max(servo0_safe_min + self.jaw_safety_margin, min(servo0_safe_max - self.jaw_safety_margin, servo0_angle))
                servo1_angle = max(servo1_safe_min + self.jaw_safety_margin, min(servo1_safe_max - self.jaw_safety_margin, servo1_angle))
            else:
                # 非交互场景使用完整范围
                servo0_angle = max(servo0_safe_min, min(servo0_safe_max, servo0_angle))
                servo1_angle = max(servo1_safe_min, min(servo1_safe_max, servo1_angle))
            
            servo0_angle = int(servo0_angle)
            servo1_angle = int(servo1_angle)
            
            if verbose:
                self.log(f"最终servo0_angle: {servo0_angle}")
                self.log(f"最终servo1_angle: {servo1_angle}")
            
            # 使用新的JS同步命令（Jaw Sync），实现真正的同步控制
            if verbose:
                self.log(f"使用JS同步命令控制下颚舵机，角度: {angle}")
            # 构建JS命令：JS<angle>，例如JS90
            js_command = f"JS{angle}\n"
            if verbose:
                self.log(f"发送JS同步命令: {js_command.strip()}")
            
            try:
                if self.is_connected and self.serial_port:
                    # 发送命令
                    self.serial_port.write(js_command.encode('utf-8'))
                    result = True
                    if wait_response:
                        # 如果需要等待响应，读取ESP32的反馈
                        response = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                        if verbose:
                            self.log(f"收到ESP32响应: {response}")
                else:
                    result = False
            except Exception as e:
                if verbose:
                    self.log(f"发送JS同步命令时出错: {str(e)}", "ERROR")
                result = False
            
            if not result:
                if verbose:
                    self.log(f"下颚舵机批量命令发送失败", "WARNING")
                return False
            
            # 更新内部状态
            if verbose:
                self.log(f"更新内部状态")
            self.servo_angles[0] = servo0_angle
            self.servo_angles[1] = servo1_angle
            
            if verbose:
                self.log(f"同时控制下颚舵机0到 {servo0_angle}°，舵机1到 {servo1_angle}°（反向运动）")
                self.log(f"===== send_jaw_servo_commands 结束 =====")
            return True
        except Exception as e:
            self.log(f"发送下颚舵机命令时出错: {str(e)}", "ERROR")
            import traceback
            self.log(f"错误详情: {traceback.format_exc()}", "ERROR")
            return False
    
    def _send_jaw_angles_debounced(self):
        self.jaw_send_after_id = None
        if not self.is_connected:
            return
        if self._pending_jaw_angle is None:
            return
        angle = int(self._pending_jaw_angle)
        self.send_jaw_servo_commands(angle, wait_response=False, verbose=False)
    
    def send_upper_mouth_corner_commands(self, angle):
        """同时发送命令到上嘴角组舵机（舵机2和3）"""
        try:
            # 右上唇（舵机2）和左上唇（舵机3）需要反向运动
            servo2_angle = angle
            
            # 计算舵机3的角度：基于相对中间值的偏移量
            # 舵机2: min=56, max=98, mid=79
            # 舵机3: min=38, max=75, mid=55
            servo2_min = self.servo_config.get('servo_2_min', 56)
            servo2_max = self.servo_config.get('servo_2_max', 98)
            servo2_mid = self.servo_config.get('servo_2_mid', 79)
            
            servo3_min = self.servo_config.get('servo_3_min', 38)
            servo3_max = self.servo_config.get('servo_3_max', 75)
            servo3_mid = self.servo_config.get('servo_3_mid', 55)
            
            # 计算舵机2相对于中间值的偏移量（百分比）
            if servo2_max == servo2_min:
                offset_percent = 0
            else:
                offset_percent = (servo2_angle - servo2_mid) / (servo2_max - servo2_min)
            
            # 将偏移量应用到舵机3，方向相反
            servo3_angle = servo3_mid - (offset_percent * (servo3_max - servo3_min))
            
            # 确保角度在安全范围内
            servo3_angle = max(servo3_min, min(servo3_max, servo3_angle))
            servo3_angle = int(servo3_angle)
            
            success = self.send_batch_commands([(2, servo2_angle), (3, servo3_angle)], wait_response=False)  # 不等待响应，提高同步性
            if not success:
                self.log("批量命令不受支持，回退为同时发送单命令", "WARNING")
                # 同时发送两个命令，不等待中间响应，提高同步性
                s2 = self.send_servo_command(2, servo2_angle, wait_response=False)
                s3 = self.send_servo_command(3, servo3_angle, wait_response=False)
                # 等待一小段时间确保命令都已发送
                time.sleep(0.05)
                success = s2 and s3
            
            # 更新内部状态
            self.servo_angles[2] = servo2_angle
            self.servo_angles[3] = servo3_angle
            
            if success:
                self.log(f"同时控制上嘴角组舵机2到 {servo2_angle}°，舵机3到 {servo3_angle}°（反向运动）")
            else:
                self.log(f"部分上嘴角组舵机命令发送失败", "WARNING")
        except Exception as e:
            self.log(f"发送上嘴角组舵机命令时出错: {str(e)}", "ERROR")
    
    def send_lower_mouth_corner_commands(self, angle):
        """同时发送命令到下嘴角组舵机（舵机4和5）"""
        try:
            # 右下唇（舵机4）和左下唇（舵机5）需要反向运动
            servo4_angle = angle
            
            # 计算舵机5的角度：基于相对中间值的偏移量
            # 舵机4: min=82, max=137, mid=109
            # 舵机5: min=35, max=95, mid=62
            servo4_min = self.servo_config.get('servo_4_min', 82)
            servo4_max = self.servo_config.get('servo_4_max', 137)
            servo4_mid = self.servo_config.get('servo_4_mid', 109)
            
            servo5_min = self.servo_config.get('servo_5_min', 35)
            servo5_max = self.servo_config.get('servo_5_max', 95)
            servo5_mid = self.servo_config.get('servo_5_mid', 62)
            
            # 计算舵机4相对于中间值的偏移量（百分比）
            if servo4_max == servo4_min:
                offset_percent = 0
            else:
                offset_percent = (servo4_angle - servo4_mid) / (servo4_max - servo4_min)
            
            # 将偏移量应用到舵机5，方向相反
            servo5_angle = servo5_mid - (offset_percent * (servo5_max - servo5_min))
            
            # 确保角度在安全范围内
            servo5_angle = max(servo5_min, min(servo5_max, servo5_angle))
            servo5_angle = int(servo5_angle)
            
            success = self.send_batch_commands([(4, servo4_angle), (5, servo5_angle)], wait_response=True)
            if not success:
                self.log("批量命令不受支持，回退为连续单命令", "WARNING")
                s4 = self.send_servo_command(4, servo4_angle, wait_response=True)
                s5 = self.send_servo_command(5, servo5_angle, wait_response=True)
                success = s4 and s5
            
            # 更新内部状态
            self.servo_angles[4] = servo4_angle
            self.servo_angles[5] = servo5_angle
            
            if success:
                self.log(f"同时控制下嘴角组舵机4到 {servo4_angle}°，舵机5到 {servo5_angle}°（反向运动）")
            else:
                self.log(f"部分下嘴角组舵机命令发送失败", "WARNING")
        except Exception as e:
            self.log(f"发送下嘴角组舵机命令时出错: {str(e)}", "ERROR")
    
    def send_upper_eyelid_commands(self, angle):
        """同时发送命令到上眼睑组舵机（舵机6和7）"""
        try:
            # 右上眼睑（舵机6）和左上眼睑（舵机7）需要反向运动
            servo6_angle = angle
            
            # 计算舵机7的角度：基于相对中间值的偏移量
            # 舵机6: min=63, max=123, mid=93
            # 舵机7: min=25, max=106, mid=66
            servo6_min = self.servo_config.get('servo_6_min', 63)
            servo6_max = self.servo_config.get('servo_6_max', 123)
            servo6_mid = self.servo_config.get('servo_6_mid', 93)
            
            servo7_min = self.servo_config.get('servo_7_min', 25)
            servo7_max = self.servo_config.get('servo_7_max', 106)
            servo7_mid = self.servo_config.get('servo_7_mid', 66)
            
            # 计算舵机6相对于中间值的偏移量（百分比）
            if servo6_max == servo6_min:
                offset_percent = 0
            else:
                offset_percent = (servo6_angle - servo6_mid) / (servo6_max - servo6_min)
            
            # 将偏移量应用到舵机7，方向相反
            servo7_angle = servo7_mid - (offset_percent * (servo7_max - servo7_min))
            
            # 确保角度在安全范围内
            servo7_angle = max(servo7_min, min(servo7_max, servo7_angle))
            servo7_angle = int(servo7_angle)
            
            success = self.send_batch_commands([(6, servo6_angle), (7, servo7_angle)], wait_response=True)
            if not success:
                self.log("批量命令不受支持，回退为连续单命令", "WARNING")
                s6 = self.send_servo_command(6, servo6_angle, wait_response=True)
                s7 = self.send_servo_command(7, servo7_angle, wait_response=True)
                success = s6 and s7
            
            # 更新内部状态
            self.servo_angles[6] = servo6_angle
            self.servo_angles[7] = servo7_angle
            
            if success:
                self.log(f"同时控制上眼睑组舵机6到 {servo6_angle}°，舵机7到 {servo7_angle}°（反向运动）")
            else:
                self.log(f"部分上眼睑组舵机命令发送失败", "WARNING")
        except Exception as e:
            self.log(f"发送上眼睑组舵机命令时出错: {str(e)}", "ERROR")
    
    def send_lower_eyelid_commands(self, angle):
        """同时发送命令到下眼睑组舵机（舵机8和9）"""
        try:
            # 右下眼睑（舵机8）和左下眼睑（舵机9）需要反向运动
            servo8_angle = angle
            
            # 计算舵机9的角度：基于相对中间值的偏移量
            # 舵机8: min=99, max=163, mid=132
            # 舵机9: min=61, max=103, mid=79
            servo8_min = self.servo_config.get('servo_8_min', 99)
            servo8_max = self.servo_config.get('servo_8_max', 163)
            servo8_mid = self.servo_config.get('servo_8_mid', 132)
            
            servo9_min = self.servo_config.get('servo_9_min', 61)
            servo9_max = self.servo_config.get('servo_9_max', 103)
            servo9_mid = self.servo_config.get('servo_9_mid', 79)
            
            # 计算舵机8相对于中间值的偏移量（百分比）
            if servo8_max == servo8_min:
                offset_percent = 0
            else:
                offset_percent = (servo8_angle - servo8_mid) / (servo8_max - servo8_min)
            
            # 将偏移量应用到舵机9，方向相反
            servo9_angle = servo9_mid - (offset_percent * (servo9_max - servo9_min))
            
            # 确保角度在安全范围内
            servo9_angle = max(servo9_min, min(servo9_max, servo9_angle))
            servo9_angle = int(servo9_angle)
            
            success = self.send_batch_commands([(8, servo8_angle), (9, servo9_angle)], wait_response=True)
            if not success:
                self.log("批量命令不受支持，回退为连续单命令", "WARNING")
                s8 = self.send_servo_command(8, servo8_angle, wait_response=True)
                s9 = self.send_servo_command(9, servo9_angle, wait_response=True)
                success = s8 and s9
            
            # 更新内部状态
            self.servo_angles[8] = servo8_angle
            self.servo_angles[9] = servo9_angle
            
            if success:
                self.log(f"同时控制下眼睑组舵机8到 {servo8_angle}°，舵机9到 {servo9_angle}°（反向运动）")
            else:
                self.log(f"部分下眼睑组舵机命令发送失败", "WARNING")
        except Exception as e:
            self.log(f"发送下眼睑组舵机命令时出错: {str(e)}", "ERROR")
    
    def send_eyebrow_commands(self, servo_id, angle):
        """同时发送命令到眉毛组舵机（根据输入的舵机ID确定组）"""
        try:
            if servo_id == 12 or servo_id == 14:
                # 眉梢组：12和14需要反向运动
                if servo_id == 12:
                    servo12_angle = angle
                    
                    # 计算舵机14的角度：基于相对中间值的偏移量
                    # 舵机12: min=66, max=103, mid=86
                    # 舵机14: min=68, max=112, mid=87
                    servo12_min = self.servo_config.get('servo_12_min', 66)
                    servo12_max = self.servo_config.get('servo_12_max', 103)
                    servo12_mid = self.servo_config.get('servo_12_mid', 86)
                    
                    servo14_min = self.servo_config.get('servo_14_min', 68)
                    servo14_max = self.servo_config.get('servo_14_max', 112)
                    servo14_mid = self.servo_config.get('servo_14_mid', 87)
                    
                    # 计算舵机12相对于中间值的偏移量（百分比）
                    if servo12_max == servo12_min:
                        offset_percent = 0
                    else:
                        offset_percent = (servo12_angle - servo12_mid) / (servo12_max - servo12_min)
                    
                    # 将偏移量应用到舵机14，方向相反
                    servo14_angle = servo14_mid - (offset_percent * (servo14_max - servo14_min))
                    
                    # 确保角度在安全范围内
                    servo14_angle = max(servo14_min, min(servo14_max, servo14_angle))
                    servo14_angle = int(servo14_angle)
                else:
                    servo14_angle = angle
                    
                    # 计算舵机12的角度：基于相对中间值的偏移量
                    servo14_min = self.servo_config.get('servo_14_min', 68)
                    servo14_max = self.servo_config.get('servo_14_max', 112)
                    servo14_mid = self.servo_config.get('servo_14_mid', 87)
                    
                    servo12_min = self.servo_config.get('servo_12_min', 66)
                    servo12_max = self.servo_config.get('servo_12_max', 103)
                    servo12_mid = self.servo_config.get('servo_12_mid', 86)
                    
                    # 计算舵机14相对于中间值的偏移量（百分比）
                    if servo14_max == servo14_min:
                        offset_percent = 0
                    else:
                        offset_percent = (servo14_angle - servo14_mid) / (servo14_max - servo14_min)
                    
                    # 将偏移量应用到舵机12，方向相反
                    servo12_angle = servo12_mid - (offset_percent * (servo12_max - servo12_min))
                    
                    # 确保角度在安全范围内
                    servo12_angle = max(servo12_min, min(servo12_max, servo12_angle))
                    servo12_angle = int(servo12_angle)
                
                success = self.send_batch_commands([(12, servo12_angle), (14, servo14_angle)], wait_response=False)  # 不等待响应，提高同步性
                if not success:
                    self.log("批量命令不受支持，回退为同时发送单命令", "WARNING")
                    # 同时发送两个命令，不等待中间响应，提高同步性
                    s12 = self.send_servo_command(12, servo12_angle, wait_response=False)
                    s14 = self.send_servo_command(14, servo14_angle, wait_response=False)
                    # 等待一小段时间确保命令都已发送
                    time.sleep(0.05)
                    success = s12 and s14
                
                # 更新内部状态
                self.servo_angles[12] = servo12_angle
                self.servo_angles[14] = servo14_angle
                
                if success:
                    self.log(f"同时控制眉梢组舵机12到 {servo12_angle}°，舵机14到 {servo14_angle}°（反向运动）")
                else:
                    self.log(f"部分眉梢组舵机命令发送失败", "WARNING")
            elif servo_id == 13 or servo_id == 15:
                # 眉头组：13和15需要反向运动
                if servo_id == 13:
                    servo13_angle = angle
                    
                    # 计算舵机15的角度：基于相对中间值的偏移量
                    # 舵机13: min=35, max=89, mid=59
                    # 舵机15: min=106, max=136, mid=121
                    servo13_min = self.servo_config.get('servo_13_min', 35)
                    servo13_max = self.servo_config.get('servo_13_max', 89)
                    servo13_mid = self.servo_config.get('servo_13_mid', 59)
                    
                    servo15_min = self.servo_config.get('servo_15_min', 106)
                    servo15_max = self.servo_config.get('servo_15_max', 136)
                    servo15_mid = (servo15_min + servo15_max) / 2  # 计算真实中间值
                    
                    # 计算舵机13相对于中间值的偏移量（百分比）
                    if servo13_max == servo13_min:
                        offset_percent = 0
                    else:
                        offset_percent = (servo13_angle - servo13_mid) / (servo13_max - servo13_min)
                    
                    # 将偏移量应用到舵机15，方向相反
                    servo15_angle = servo15_mid - (offset_percent * (servo15_max - servo15_min))
                    
                    # 确保角度在安全范围内
                    servo15_angle = max(servo15_min, min(servo15_max, servo15_angle))
                    servo15_angle = int(servo15_angle)
                else:
                    servo15_angle = angle
                    
                    # 计算舵机13的角度：基于相对中间值的偏移量
                    servo15_min = self.servo_config.get('servo_15_min', 106)
                    servo15_max = self.servo_config.get('servo_15_max', 136)
                    servo15_mid = (servo15_min + servo15_max) / 2  # 计算真实中间值
                    
                    servo13_min = self.servo_config.get('servo_13_min', 35)
                    servo13_max = self.servo_config.get('servo_13_max', 89)
                    servo13_mid = self.servo_config.get('servo_13_mid', 59)
                    
                    # 计算舵机15相对于中间值的偏移量（百分比）
                    if servo15_max == servo15_min:
                        offset_percent = 0
                    else:
                        offset_percent = (servo15_angle - servo15_mid) / (servo15_max - servo15_min)
                    
                    # 将偏移量应用到舵机13，方向相反
                    servo13_angle = servo13_mid - (offset_percent * (servo13_max - servo13_min))
                    
                    # 确保角度在安全范围内
                    servo13_angle = max(servo13_min, min(servo13_max, servo13_angle))
                    servo13_angle = int(servo13_angle)
                
                success = self.send_batch_commands([(13, servo13_angle), (15, servo15_angle)], wait_response=False)  # 不等待响应，提高同步性
                if not success:
                    self.log("批量命令不受支持，回退为同时发送单命令", "WARNING")
                    # 同时发送两个命令，不等待中间响应，提高同步性
                    s13 = self.send_servo_command(13, servo13_angle, wait_response=False)
                    s15 = self.send_servo_command(15, servo15_angle, wait_response=False)
                    # 等待一小段时间确保命令都已发送
                    time.sleep(0.05)
                    success = s13 and s15
                
                # 更新内部状态
                self.servo_angles[13] = servo13_angle
                self.servo_angles[15] = servo15_angle
                
                if success:
                    self.log(f"同时控制眉头组舵机13到 {servo13_angle}°，舵机15到 {servo15_angle}°（反向运动）")
                else:
                    self.log(f"部分眉头组舵机命令发送失败", "WARNING")
        except Exception as e:
            self.log(f"发送眉毛组舵机命令时出错: {str(e)}", "ERROR")
    
    def set_jaw_servo_init(self, init_var):
        """从滑条读取当前角度并设置为下颚舵机最小角度"""
        try:
            # 读取当前滑条的度数
            if hasattr(self, 'jaw_angle_var'):
                current_angle = int(self.jaw_angle_var.get())
            elif 0 in self.servo_controls:
                current_angle = int(self.servo_controls[0]['var'].get())
            else:
                current_angle = 90
            
            if 0 <= current_angle <= 180:
                # 保存到配置文件
                self.servo_config['servo_0_min'] = current_angle
                self.servo_config['servo_1_min'] = current_angle
                self.save_config()
                
                # 更新输入框显示
                init_var.set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[0] = current_angle
                self.servo_angles[1] = current_angle
                self.log(f"下颚舵机最小角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置下颚舵机最小角度失败: {str(e)}", "ERROR")
    
    def set_jaw_servo_end(self, end_var):
        """从滑条读取当前角度并设置为下颚舵机最大角度"""
        try:
            # 读取当前滑条的度数
            if hasattr(self, 'jaw_angle_var'):
                current_angle = int(self.jaw_angle_var.get())
            elif 0 in self.servo_controls:
                current_angle = int(self.servo_controls[0]['var'].get())
            else:
                current_angle = 90
            
            if 0 <= current_angle <= 180:
                # 保存到配置文件
                self.servo_config['servo_0_max'] = current_angle
                self.servo_config['servo_1_max'] = current_angle
                self.save_config()
                
                # 更新输入框显示
                end_var.set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[0] = current_angle
                self.servo_angles[1] = current_angle
                self.log(f"下颚舵机最大角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置下颚舵机最大角度失败: {str(e)}", "ERROR")
    
    def set_jaw_servo_mid(self, mid_var):
        """从滑条读取当前角度并设置为下颚舵机中间角度"""
        try:
            # 读取当前滑条的度数
            if hasattr(self, 'jaw_angle_var'):
                current_angle = int(self.jaw_angle_var.get())
            elif 0 in self.servo_controls:
                current_angle = int(self.servo_controls[0]['var'].get())
            else:
                current_angle = 90
            
            if 0 <= current_angle <= 180:
                # 保存到配置文件
                self.servo_config['servo_0_mid'] = current_angle
                self.servo_config['servo_1_mid'] = current_angle
                self.save_config()
                
                # 更新输入框显示
                mid_var.set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[0] = current_angle
                self.servo_angles[1] = current_angle
                self.log(f"下颚舵机中间角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置下颚舵机中间角度失败: {str(e)}", "ERROR")
    
    def send_servo_command(self, servo_id, angle, wait_response=True):
        """发送舵机控制命令
        
        Args:
            servo_id: 舵机ID
            angle: 角度值
            wait_response: 是否等待响应（默认是）
            
        Returns:
            命令是否发送成功
        """
        if not self.serial_port or not self.is_connected:
            self.log(f"错误: 串口未连接，无法发送命令 S{servo_id},{angle}", "ERROR")
            return False
        
        try:
            smin = self.servo_config.get(f'servo_{servo_id}_min', 0)
            smax = self.servo_config.get(f'servo_{servo_id}_max', 180)
            if smin > smax:
                smin, smax = smax, smin
            if angle < smin:
                angle = smin
            elif angle > smax:
                angle = smax
            if angle < 0:
                angle = 0
            elif angle > 180:
                angle = 180
            
            # 构建命令
            command = f"S{servo_id},{angle}"
            
            # 发送命令（使用CRLF结束符）
            full_command = command + '\n'
            self.serial_port.write(full_command.encode())
            self.log(f"发送命令: {command}")
            
            if wait_response:
                # 等待响应
                time.sleep(0.2)
                
                # 读取并显示所有响应行，但不进行复杂的响应处理
                while self.serial_port.in_waiting:
                    response = self.serial_port.readline().decode().strip()
                    if response:
                        self.log(f"ESP32响应: {response}")
                        # 如果找到ERROR响应，返回False
                        if response.startswith("ERROR"):
                            return False
                
                # 无论是否找到OK响应，都假设命令发送成功
                # 因为ESP32的DEBUG信息已经表明命令被正确处理
                return True
            else:
                # 不等待响应，立即返回成功
                return True
            
        except serial.SerialException as e:
            self.log(f"串口错误: {e}", "ERROR")
            self.is_connected = False
            self.connect_btn.config(text="连接")
            self.status_label.config(text="未连接", foreground="red")
            return False
        except Exception as e:
            self.log(f"发送命令失败: {e}", "ERROR")
            return False
        
    def send_batch_commands(self, commands, wait_response=True):
        if not self.serial_port or not self.is_connected:
            return False
        if not commands:
            return True
        try:
            parts = []
            for ch, ang in commands:
                if ang < 0:
                    ang = 0
                elif ang > 180:
                    ang = 180
                parts.append(f"{int(ch)},{int(ang)}")
            full_command = "S" + ";".join(parts) + "\n"
            self.serial_port.write(full_command.encode())
            if wait_response:
                self.log(f"发送批量命令: {full_command.strip()}")
            if wait_response:
                time.sleep(0.2)
                while self.serial_port.in_waiting:
                    response = self.serial_port.readline().decode().strip()
                    if response:
                        self.log(f"ESP32响应: {response}")
                        if response.startswith("ERROR"):
                            return False
                return True
            else:
                return True
        except Exception as e:
            self.log(f"发送批量命令失败: {e}", "ERROR")
            return False
                
    def run_script(self):
        """运行脚本"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return
            
        if self.running_script:
            messagebox.showinfo("提示", "脚本正在运行中")
            return
            
        self.running_script = True
        self.script_thread = threading.Thread(target=self.execute_script_with_reset, daemon=True)
        self.script_thread.start()
        
    def execute_script_with_reset(self):
        """执行脚本前先自动归零"""
        # 脚本运行前自动执行全部归零
        self.log("脚本运行前自动执行全部归零...")
        self.reset_all_servos()
        time.sleep(1)  # 等待归零完成
        
        # 然后执行正常脚本
        self.execute_script()
        
    def execute_script(self):
        """逐行执行脚本"""
        try:
            # 获取脚本内容
            script_content = self.script_text.get("1.0", tk.END).strip()
            if not script_content:
                self.log("脚本内容为空")
                self.running_script = False
                return
                
            # 按行分割脚本
            lines = script_content.split('\n')
            
            # 逐行执行
            for line_num, line in enumerate(lines, 1):
                if not self.running_script:
                    self.log("脚本执行被停止")
                    break
                    
                line = line.strip()
                
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                    
                # 高亮显示当前执行行
                self.highlight_line(line_num)
                
                # 解析命令
                if line.startswith('舵机'):
                    # 舵机控制命令: 舵机X 角度
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            servo_id = int(parts[0][2:])  # 提取舵机编号
                            angle = int(parts[1])
                            
                            if 0 <= servo_id < 16 and 0 <= angle <= 180:
                                self.log(f"执行: {line}")
                                
                                # 根据舵机分组处理
                                if servo_id == 0 or servo_id == 1:
                                    # 下颚组：0和1需要同步反向运行
                                    self.send_jaw_servo_commands(angle)
                                elif servo_id == 2 or servo_id == 3:
                                    # 上嘴角组：2和3需要同步运行
                                    self.send_upper_mouth_corner_commands(angle)
                                elif servo_id == 4 or servo_id == 5:
                                    # 下嘴角组：4和5需要同步运行
                                    self.send_lower_mouth_corner_commands(angle)
                                elif servo_id == 6 or servo_id == 7:
                                    # 上眼睑组：6和7需要同步运行
                                    self.send_upper_eyelid_commands(angle)
                                elif servo_id == 8 or servo_id == 9:
                                    # 下眼睑组：8和9需要同步运行
                                    self.send_lower_eyelid_commands(angle)
                                elif servo_id == 12 or servo_id == 13 or servo_id == 14 or servo_id == 15:
                                    # 眉毛组：12-15需要同步运行
                                    self.send_eyebrow_commands(servo_id, angle)
                                else:
                                    # 单独控制的舵机
                                    success = self.send_servo_command(servo_id, angle)
                                    
                                # 更新GUI
                                self.update_servo_gui(servo_id, angle)
                                time.sleep(0.1)
                            else:
                                self.log(f"无效命令: {line}", "WARNING")
                        except ValueError:
                            self.log(f"命令格式错误: {line}", "WARNING")
                    else:
                        self.log(f"命令格式错误: {line}", "WARNING")
                        
                elif line.startswith('延时'):
                    # 延时命令: 延时 毫秒数
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            delay_ms = int(parts[1])
                            self.log(f"延时 {delay_ms}ms")
                            # 延时期间检查停止标志
                            for _ in range(delay_ms // 100):
                                if not self.running_script:
                                    break
                                time.sleep(0.1)
                        except ValueError:
                            self.log(f"延时格式错误: {line}", "WARNING")
                    else:
                        self.log(f"延时格式错误: {line}", "WARNING")
                        
                else:
                    self.log(f"未知命令: {line}", "WARNING")
                    
            # 清除高亮
            self.clear_highlight()
            
            if self.running_script:
                self.log("脚本执行完成")
                
                # 脚本完成后自动执行全部归零
                self.log("脚本完成后自动执行全部归零...")
                self.reset_all_servos()
                
            self.running_script = False
                
        except Exception as e:
            self.log(f"脚本执行出错: {e}", "ERROR")
            self.running_script = False
            self.clear_highlight()
        
    def highlight_line(self, line_num):
        """高亮显示当前执行行"""
        # 清除之前的高亮
        self.clear_highlight()
        
        # 设置当前行高亮
        start_index = f"{line_num}.0"
        end_index = f"{line_num}.end"
        self.script_text.tag_add("current_line", start_index, end_index)
        self.script_text.tag_config("current_line", background="yellow")
        
        # 滚动到当前行
        self.script_text.see(start_index)
        
    def clear_highlight(self):
        """清除所有高亮"""
        self.script_text.tag_remove("current_line", "1.0", tk.END)
        
    def update_servo_gui(self, servo_id, angle):
        """更新舵机GUI显示"""
        if 0 <= servo_id < 16 and servo_id < len(self.servo_controls):
            if self.servo_controls[servo_id]:
                self.servo_controls[servo_id]['var'].set(angle)
                self.servo_controls[servo_id]['label'].config(text=f"{angle}°")
                self.servo_angles[servo_id] = angle
        
    def stop_script(self):
        """停止脚本执行"""
        self.running_script = False
        self.log("正在停止脚本...")
        
    def save_script(self):
        """保存脚本"""
        script_name = self.script_name_var.get().strip()
        if not script_name:
            script_name = "未命名"
            self.script_name_var.set(script_name)
            
        script_content = self.script_text.get("1.0", tk.END).strip()
        
        if not script_content:
            self.log("脚本内容为空，无法保存", "WARNING")
            return
            
        try:
            # 加载现有脚本
            if os.path.exists(self.script_file):
                with open(self.script_file, 'r', encoding='utf-8') as f:
                    scripts = json.load(f)
            else:
                scripts = {}
            
            # 保存脚本
            scripts[script_name] = script_content
            
            with open(self.script_file, 'w', encoding='utf-8') as f:
                json.dump(scripts, f, ensure_ascii=False, indent=2)
            
            # 保存最后使用的脚本名称
            self.servo_config['last_script'] = script_name
            self.save_config()
            
            self.log(f"脚本 '{script_name}' 已保存")
            
        except Exception as e:
            self.log(f"保存脚本失败: {e}", "ERROR")
    
    def load_last_script(self):
        """加载上次最后使用的脚本"""
        try:
            last_script_name = self.servo_config.get('last_script', '')
            
            if last_script_name and os.path.exists(self.script_file):
                with open(self.script_file, 'r', encoding='utf-8') as f:
                    scripts = json.load(f)
                
                if last_script_name in scripts:
                    self.script_name_var.set(last_script_name)
                    self.script_text.delete("1.0", tk.END)
                    self.script_text.insert("1.0", scripts[last_script_name])
                    self.log(f"已加载上次脚本: {last_script_name}")
                    return
            
            # 如果没有上次脚本，插入示例脚本
            self.insert_example()
            
        except Exception as e:
            self.log(f"加载上次脚本失败: {e}", "ERROR")
            # 出错时插入示例脚本
            self.insert_example()
    
    def load_script_dialog(self):
        """加载脚本对话框 - 从文件系统选择脚本文件"""
        try:
            # 默认打开表情脚本文件夹
            default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "表情脚本")
            if not os.path.exists(default_dir):
                default_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 使用文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择脚本文件",
                initialdir=default_dir,
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("JSON文件", "*.json"),
                    ("所有文件", "*.*")
                ]
            )
            
            if file_path:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 设置脚本名称为文件名（不含扩展名）
                script_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 更新界面
                self.script_name_var.set(script_name)
                self.script_text.delete("1.0", tk.END)
                self.script_text.insert("1.0", content)
                
                # 保存最后使用的脚本名称
                self.servo_config['last_script'] = script_name
                self.save_config()
                
                self.log(f"已加载脚本: {script_name} ({file_path})")
        except Exception as e:
            self.log(f"加载脚本失败: {e}", "ERROR")
            
    def load_scripts(self):
        """加载保存的脚本"""
        if os.path.exists(self.script_file):
            try:
                with open(self.script_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def new_script(self):
        """新建脚本"""
        self.script_name_var.set("未命名")
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert(tk.END, "# 新脚本\n# 延时单位：毫秒(ms)\n\n")
        self.log("创建新脚本")
        
    def load_config(self):
        """加载舵机配置文件"""
        config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                self.log(f"加载配置文件失败: {str(e)}", "ERROR")
        
        # 确保每个舵机都有默认配置
        for i in range(16):
            # 兼容旧配置，优先使用新键名，不存在则使用旧键名
            if f'servo_{i}_min' not in config:
                config[f'servo_{i}_min'] = config.get(f'servo_{i}_init', 90)
            if f'servo_{i}_max' not in config:
                config[f'servo_{i}_max'] = config.get(f'servo_{i}_end', 90)
            if f'servo_{i}_mid' not in config:
                config[f'servo_{i}_mid'] = 90
                
        return config
    
    def on_closing(self):
        """窗口关闭事件处理"""
        try:
            # 保存当前配置
            if self.save_config():
                self.log("配置已保存", "INFO")
            else:
                self.log("配置保存失败", "ERROR")
        except Exception as e:
            self.log(f"关闭时保存配置失败: {e}", "ERROR")
        finally:
            # 关闭串口连接
            if hasattr(self, 'serial_port') and self.serial_port and hasattr(self.serial_port, 'is_open') and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    pass
            # 销毁窗口
            self.root.destroy()

    def toggle_auto_send_angles(self):
        """切换连接后是否自动发送角度的配置"""
        self.servo_config['auto_send_angles'] = self.auto_send_var.get()
        if self.save_config():
            self.log(f"已{'' if self.auto_send_var.get() else '关闭'}连接后自动发送角度功能")
        else:
            self.log("保存配置失败", "ERROR")
    
    def initialize_servos(self):
        """初始化所有舵机到中间位置（不更新GUI滑条）"""
        try:
            if not self.is_connected:
                messagebox.showwarning("警告", "请先连接串口")
                return
            
            self.log("开始初始化所有舵机到中间位置...")
            
            # 发送RESET命令到ESP32，让硬件统一处理所有舵机的初始化
            self.serial_port.write(b"RESET\n")
            self.log("已发送RESET命令到硬件，等待所有舵机移动到中间位置...")
            time.sleep(1.5)  # 等待所有舵机移动完成
            
            self.log("所有舵机已初始化到中间位置")
        except Exception as e:
            self.log(f"初始化舵机过程中发生错误: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"初始化失败: {str(e)}")
    

    
    def save_config(self):
        """保存舵机配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.servo_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log(f"保存配置失败: {e}", "ERROR")
            return False
    
    def set_servo_min(self, servo_id):
        try:
            self.suppress_send = True
            if self.jaw_send_after_id is not None:
                try:
                    self.root.after_cancel(self.jaw_send_after_id)
                except Exception:
                    pass
                self.jaw_send_after_id = None
            # 读取当前滑条的度数
            current_angle = int(self.servo_controls[servo_id]['var'].get())
            
            if 0 <= current_angle <= 180:
                # 获取当前的最大角度
                current_max = self.servo_config.get(f'servo_{servo_id}_max', 180)
                
                # 确保最小角度小于最大角度
                if current_angle >= current_max:
                    # 如果设置的最小角度大于等于当前最大角度，自动调整最大角度
                    new_max = max(current_angle + 1, 180)
                    self.servo_config[f'servo_{servo_id}_max'] = new_max
                    
                    # 如果是下颚舵机(servo_id=0或1)，确保两者的最大角度一致
                    if servo_id == 0 or servo_id == 1:
                        self.servo_config['servo_0_max'] = new_max
                        self.servo_config['servo_1_max'] = new_max
                
                # 保存最小角度到配置文件
                self.servo_config[f'servo_{servo_id}_min'] = current_angle
                
                # 如果是下颚舵机(servo_id=0或1)，确保两者的最小角度符合反向同步要求
                if servo_id == 0:
                    self.servo_config['servo_0_min'] = current_angle
                    # 对于舵机1，其有效角度是与舵机0反向的，所以不需要设置相同的最小角度
                elif servo_id == 1:
                    self.servo_config['servo_1_min'] = current_angle
                    
                self.save_config()
                
                # 更新输入框显示
                if servo_id == 0:
                    # 下颚舵机使用init_var
                    self.servo_controls[servo_id]['init_var'].set(str(current_angle))
                else:
                    # 普通舵机使用min_var
                    self.servo_controls[servo_id]['min_var'].set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[servo_id] = current_angle
                if servo_id == 0:
                    # 对于下颚舵机，保持反向同步，舵机1的角度应该是180°-舵机0的角度
                    self.servo_angles[1] = 180 - current_angle
                elif servo_id == 1:
                    # 对于舵机1，舵机0的角度应该是180°-舵机1的角度
                    self.servo_angles[0] = 180 - current_angle
                
                # 只更新当前被修改的舵机的滑条范围
                self.update_servo_scales(servo_id)
                
                self.log(f"舵机{servo_id} 最小角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置最小角度失败: {str(e)}", "ERROR")
        finally:
            self.suppress_send = False
            # 发送当前角度命令，确保舵机处于正确位置
            if self.is_connected:
                if servo_id == 0 or servo_id == 1:
                    self.send_jaw_servo_commands(current_angle, wait_response=False, verbose=False)
    
    def set_servo_max(self, servo_id):
        try:
            self.suppress_send = True
            if self.jaw_send_after_id is not None:
                try:
                    self.root.after_cancel(self.jaw_send_after_id)
                except Exception:
                    pass
                self.jaw_send_after_id = None
            # 读取当前滑条的度数
            current_angle = int(self.servo_controls[servo_id]['var'].get())
            
            if 0 <= current_angle <= 180:
                # 获取当前的最小角度
                current_min = self.servo_config.get(f'servo_{servo_id}_min', 0)
                
                # 确保最大角度大于最小角度
                if current_angle <= current_min:
                    # 如果设置的最大角度小于等于当前最小角度，自动调整最小角度
                    new_min = min(current_angle - 1, 0)
                    self.servo_config[f'servo_{servo_id}_min'] = new_min
                    
                    # 如果是下颚舵机(servo_id=0或1)，确保两者的最小角度一致
                    if servo_id == 0 or servo_id == 1:
                        self.servo_config['servo_0_min'] = new_min
                        self.servo_config['servo_1_min'] = new_min
                
                # 保存最大角度到配置文件
                self.servo_config[f'servo_{servo_id}_max'] = current_angle
                
                # 如果是下颚舵机(servo_id=0或1)，确保两者的最大角度符合反向同步要求
                if servo_id == 0:
                    self.servo_config['servo_0_max'] = current_angle
                    # 对于舵机1，其有效角度是与舵机0反向的，所以不需要设置相同的最大角度
                elif servo_id == 1:
                    self.servo_config['servo_1_max'] = current_angle
                    
                self.save_config()
                
                # 更新输入框显示
                if servo_id == 0:
                    # 下颚舵机使用end_var
                    self.servo_controls[servo_id]['end_var'].set(str(current_angle))
                else:
                    # 普通舵机使用max_var
                    self.servo_controls[servo_id]['max_var'].set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[servo_id] = current_angle
                if servo_id == 0:
                    # 对于下颚舵机，保持反向同步，舵机1的角度应该是180°-舵机0的角度
                    self.servo_angles[1] = 180 - current_angle
                elif servo_id == 1:
                    # 对于舵机1，舵机0的角度应该是180°-舵机1的角度
                    self.servo_angles[0] = 180 - current_angle
                
                # 只更新当前被修改的舵机的滑条范围
                self.update_servo_scales(servo_id)
                
                self.log(f"舵机{servo_id} 最大角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置最大角度失败: {str(e)}", "ERROR")
        finally:
            self.suppress_send = False
            # 发送当前角度命令，确保舵机处于正确位置
            if self.is_connected:
                if servo_id == 0 or servo_id == 1:
                    self.send_jaw_servo_commands(current_angle, wait_response=False, verbose=False)
    
    def set_servo_mid(self, servo_id):
        try:
            self.suppress_send = True
            if self.jaw_send_after_id is not None:
                try:
                    self.root.after_cancel(self.jaw_send_after_id)
                except Exception:
                    pass
                self.jaw_send_after_id = None
            # 读取当前滑条的度数
            current_angle = int(self.servo_controls[servo_id]['var'].get())
            
            if 0 <= current_angle <= 180:
                # 保存到配置文件
                self.servo_config[f'servo_{servo_id}_mid'] = current_angle
                
                # 如果是下颚舵机(servo_id=0或1)，确保两者的中间角度符合反向同步要求
                if servo_id == 0:
                    self.servo_config['servo_0_mid'] = current_angle
                    # 对于舵机1，其有效角度是与舵机0反向的，所以不需要设置相同的中间角度
                elif servo_id == 1:
                    self.servo_config['servo_1_mid'] = current_angle
                    
                self.save_config()
                
                # 更新输入框显示
                self.servo_controls[servo_id]['mid_var'].set(str(current_angle))
                
                # 更新GUI显示
                self.servo_angles[servo_id] = current_angle
                if servo_id == 0:
                    self.servo_angles[1] = current_angle
                
                # 只更新当前被修改的舵机的滑条范围
                self.update_servo_scales(servo_id)
                
                self.log(f"舵机{servo_id} 中间角度设置为: {current_angle}°")
            else:
                self.log("角度必须在0-180之间", "WARNING")
        except Exception as e:
            self.log(f"设置中间角度失败: {str(e)}", "ERROR")
        finally:
            self.suppress_send = False
            # 发送当前角度命令，确保舵机处于正确位置
            if self.is_connected:
                if servo_id == 0 or servo_id == 1:
                    self.send_jaw_servo_commands(current_angle, wait_response=False, verbose=False)
    
    def update_servo_scales(self, servo_id=None):
        """更新舵机滑条的范围
        
        Args:
            servo_id: 可选参数，指定要更新的特定舵机ID。如果为None，则更新所有舵机。
        """
        try:
            self.suppress_send = True
            # 确定要更新的舵机列表
            if servo_id is None:
                servo_ids = range(16)
            else:
                servo_ids = [servo_id]
                # 如果是下颚舵机(servo_id=0或1)，确保两者都更新
                if servo_id == 0 or servo_id == 1:
                    servo_ids.append(0 if servo_id == 1 else 1)
            
            # 更新普通舵机滑条范围
            for i in servo_ids:
                if i < len(self.servo_controls) and self.servo_controls[i]:
                    min_angle = self.servo_config.get(f'servo_{i}_min', 0)
                    max_angle = self.servo_config.get(f'servo_{i}_max', 180)
                    
                    # 确保min_angle < max_angle
                    if min_angle >= max_angle:
                        # 如果最小值大于等于最大值，自动调整为合理范围
                        # 保持当前值作为中间值，扩展范围
                        current_value = int(self.servo_controls[i]['var'].get())
                        min_angle = max(0, current_value - 45)
                        max_angle = min(180, current_value + 45)
                        # 更新配置文件
                        self.servo_config[f'servo_{i}_min'] = min_angle
                        self.servo_config[f'servo_{i}_max'] = max_angle
                        # 保存配置文件
                        self.save_config()
                    
                    # 更新滑条范围
                    self.servo_controls[i]['scale'].configure(from_=min_angle, to=max_angle)
                    
                    # 确保当前值在新范围内
                    current_value = int(self.servo_controls[i]['var'].get())
                    if current_value < min_angle:
                        self.servo_controls[i]['var'].set(min_angle)
                    elif current_value > max_angle:
                        self.servo_controls[i]['var'].set(max_angle)
            
            # 更新下颚舵机滑条范围（如果是下颚舵机或更新所有舵机）
            if hasattr(self, 'jaw_scale') and (servo_id is None or servo_id == 0):
                jaw_min = self.servo_config.get('servo_0_min', 0)
                jaw_max = self.servo_config.get('servo_0_max', 180)
                
                # 确保min_angle < max_angle
                if jaw_min >= jaw_max:
                    # 如果最小值大于等于最大值，自动调整为合理范围
                    # 保持当前值作为中间值，扩展范围
                    current_value = int(self.jaw_angle_var.get())
                    jaw_min = max(0, current_value - 45)
                    jaw_max = min(180, current_value + 45)
                    # 更新配置文件
                    self.servo_config['servo_0_min'] = jaw_min
                    self.servo_config['servo_0_max'] = jaw_max
                    # 保存配置文件
                    self.save_config()
                
                self.jaw_scale.configure(from_=jaw_min, to=jaw_max)
                
                # 确保当前值在新范围内
                current_value = int(self.jaw_angle_var.get())
                if current_value < jaw_min:
                    self.jaw_angle_var.set(jaw_min)
                elif current_value > jaw_max:
                    self.jaw_angle_var.set(jaw_max)
            
            if servo_id is None:
                self.log("所有舵机滑条范围已更新")
            else:
                self.log(f"舵机{servo_id}滑条范围已更新")
        except Exception as e:
            self.log(f"更新滑条范围失败: {str(e)}", "ERROR")
        finally:
            self.suppress_send = False
    
    def configure_single_servo(self):
        """单独配置指定舵机的角度范围"""
        try:
            # 获取用户输入的舵机号
            servo_id = int(self.single_servo_var.get())
            
            # 验证舵机号是否有效
            if servo_id < 0 or servo_id >= len(self.servo_controls) or not self.servo_controls[servo_id]:
                messagebox.showerror("错误", f"无效的舵机号: {servo_id}")
                return
            
            # 重置指定舵机的滑条范围到0-180°
            self.suppress_send = True
            self.servo_controls[servo_id]['scale'].configure(from_=0, to=180)
            
            # 更新配置文件中的min_angle和max_angle值为0和180
            self.servo_config[f'servo_{servo_id}_min'] = 0
            self.servo_config[f'servo_{servo_id}_max'] = 180
            
            # 如果是下颚舵机(servo_id=0或1)，确保两者都更新
            if servo_id == 0 or servo_id == 1:
                self.servo_config['servo_0_min'] = 0
                self.servo_config['servo_0_max'] = 180
                self.servo_config['servo_1_min'] = 0
                self.servo_config['servo_1_max'] = 180
            
            # 保存配置文件
            self.save_config()
            
            # 更新输入框显示为0-180范围
            if servo_id == 0:  # 下颚舵机
                self.servo_controls[servo_id]['init_var'].set('0')
                self.servo_controls[servo_id]['end_var'].set('180')
            else:  # 其他舵机
                self.servo_controls[servo_id]['min_var'].set('0')
                self.servo_controls[servo_id]['max_var'].set('180')
            
            # 提示用户可以开始配置指定舵机
            messagebox.showinfo("提示", f"舵机{servo_id}的滑条范围已重置为0-180°\n" +
                               "现在可以配置该舵机的'最小角度'、'最大角度'和'中间值'\n" +
                               "修改完成后，点击'保存所有配置'按钮保存所有配置")
            
            self.log(f"已重置舵机{servo_id}的滑条范围为0-180°，进入配置模式")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字作为舵机号")
        except Exception as e:
            self.log(f"配置舵机失败: {e}", "ERROR")
            messagebox.showerror("错误", f"配置舵机失败: {e}")
        finally:
            self.suppress_send = False
    
    def reset_servo_scales(self):
        """重置所有舵机滑条到默认范围(0-180)"""
        try:
            self.suppress_send = True
            # 重置普通舵机滑条范围和配置
            for i in range(16):
                if i < len(self.servo_controls) and self.servo_controls[i]:
                    # 更新滑条范围
                    self.servo_controls[i]['scale'].configure(from_=0, to=180)
                    # 更新配置文件
                    self.servo_config[f'servo_{i}_min'] = 0
                    self.servo_config[f'servo_{i}_max'] = 180
                    # 更新输入框显示
                    if i == 0:
                        # 下颚舵机使用init_var/end_var
                        self.servo_controls[i]['init_var'].set('0')
                        self.servo_controls[i]['end_var'].set('180')
                    else:
                        # 普通舵机使用min_var/max_var
                        self.servo_controls[i]['min_var'].set('0')
                        self.servo_controls[i]['max_var'].set('180')
            
            # 重置下颚舵机滑条范围
            if hasattr(self, 'jaw_scale'):
                self.jaw_scale.configure(from_=0, to=180)
            
            # 保存配置文件
            self.save_config()
            
            self.log("所有舵机滑条已重置为0-180范围")
        except Exception as e:
            self.log(f"重置滑条范围失败: {str(e)}", "ERROR")
        finally:
            self.suppress_send = False
    
    def save_all_config(self):
        """保存所有舵机配置并更新滑条范围"""
        try:
            for i in range(16):
                if i < len(self.servo_controls) and self.servo_controls[i]:
                    # 获取角度值，处理下颚舵机的特殊变量命名
                    if i == 0:
                        # 下颚舵机使用init_var/end_var
                        min_angle = int(self.servo_controls[i]['init_var'].get())
                        max_angle = int(self.servo_controls[i]['end_var'].get())
                    else:
                        # 普通舵机使用min_var/max_var
                        min_angle = int(self.servo_controls[i]['min_var'].get())
                        max_angle = int(self.servo_controls[i]['max_var'].get())
                    mid_angle = int(self.servo_controls[i]['mid_var'].get())
                    
                    if 0 <= min_angle <= 180 and 0 <= max_angle <= 180 and 0 <= mid_angle <= 180:
                        if mid_angle < min_angle:
                            mid_angle = min_angle
                        elif mid_angle > max_angle:
                            mid_angle = max_angle
                        self.servo_config[f'servo_{i}_min'] = min_angle
                        self.servo_config[f'servo_{i}_max'] = max_angle
                        self.servo_config[f'servo_{i}_mid'] = mid_angle
                    else:
                        self.log(f"舵机{i}的角度必须在0-180之间", "WARNING")
                        return
            
            if self.save_config():
                self.log("所有舵机配置已保存")
                # 更新滑条范围
                self.update_servo_scales()
            else:
                self.log("保存配置失败", "ERROR")
        except ValueError:
            self.log("请输入有效的数字", "WARNING")
    
    def reset_all_servos(self):
        """将所有舵机移动到中间值"""
        try:
            self.log("开始将所有舵机移动到中间值...")
            
            if self.is_connected:
                # 发送RESET命令到ESP32，让硬件统一处理所有舵机的初始化
                self.serial_port.write(b"RESET\n")
                self.log("已发送RESET命令到硬件，等待所有舵机移动到中间位置...")
                time.sleep(1.5)  # 等待所有舵机移动完成
            
            # 更新GUI显示所有舵机的中间值
            for i in range(0, 16):
                if i < len(self.servo_controls) and self.servo_controls[i]:
                    mid_angle = int(self.servo_controls[i]['mid_var'].get())
                    min_angle = self.servo_config.get(f'servo_{i}_min', 0)
                    max_angle = self.servo_config.get(f'servo_{i}_max', 180)
                    if mid_angle < min_angle:
                        mid_angle = min_angle
                    elif mid_angle > max_angle:
                        mid_angle = max_angle
                    if 0 <= mid_angle <= 180:
                        # 更新GUI滑块位置
                        if i < 2:
                            # 下颚舵机使用统一的滑块
                            self.jaw_angle_var.set(mid_angle)
                            self.servo_controls[0]['label'].config(text=f"{mid_angle}°")
                            self.servo_angles[0] = mid_angle
                            self.servo_angles[1] = mid_angle
                        else:
                            # 其他舵机使用各自的滑块
                            self.servo_controls[i]['var'].set(mid_angle)
                            self.servo_controls[i]['label'].config(text=f"{mid_angle}°")
                            self.servo_angles[i] = mid_angle
                    else:
                        self.log(f"舵机{i}中间值超出范围: {mid_angle}°", "WARNING")
            
            self.log("所有舵机GUI已更新到中间值")
            if self.is_connected:
                self.log("所有舵机已通过硬件RESET命令移动到中间位置")
        except Exception as e:
            self.log(f"移动到中间值过程中发生错误: {str(e)}", "ERROR")
    

    
    def log(self, message, level="INFO"):
        """添加带级别的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # 输出到控制台
        print(log_message)
        
        # 根据级别设置颜色
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        if level == "ERROR":
            self.log_text.tag_add("error", "end-2c linestart", "end-1c")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", "end-2c linestart", "end-1c")
            self.log_text.tag_config("warning", foreground="orange")
        
        self.log_text.see(tk.END)
        
    

def main():
    root = tk.Tk()
    root.title("仿生人头控制系统 - 增强版")
    root.geometry("1200x1100")
    root.resizable(False, False)
    
    # 确保窗口在初始化后能正确布局所有组件
    root.update_idletasks()
    root.after(100, lambda: root.update_idletasks())
    
    app = ServoControlGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
