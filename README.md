# Embodied-Perception-Head
具身感知头（Embodied Perception Head）
项目简介
欢迎来到开源仿生人头项目！这是一个致力于设计和构建高度仿真、可交互的仿生人头的开源项目。我们的目标是创建一个平台，让爱好者、学生和研究人员能够探索机器人学、人工智能和人机交互的前沿技术。
主要特性
高度仿真的外观：采用 3D 打印技术和精细的外部处理，打造逼真的面部外观。
丰富的表情模拟：通过多舵机驱动，实现包括微笑、皱眉、惊讶、愤怒等多种复杂面部表情。
灵动的眼部运动：独立控制的眼球转动和眨眼功能，增强交互的生动性。
模块化设计：硬件和软件均采用模块化架构，便于组装、调试、维修和功能扩展。
完全开源：所有设计文件（3D 模型、电路原理图）和源代码均免费开放，鼓励社区贡献和二次开发。
硬件需求
电子元件
微控制器：推荐使用Banana Pi BPI-F3/Raspberry Pi 4 作为主控制器。
伺服电机 (Servo Motors)：
19 个标准舵机（如 SG90）用于控制面部表情。
2 个高精度舵机（如 MG996R）用于控制眼球和颈部。
电源模块：
一个 5V直流电源适配器。
一个舵机驱动板（如 PCA9685），用于扩展 PWM 输出通道。
传感器 (可选)：
摄像头模块，用于视觉输入。
麦克风模块，用于语音识别。
结构件：
3D 打印的头部骨架、面板和外壳。
用于连接和固定的螺丝、螺母、轴承等五金件。
弹性材料（如硅胶、热塑性弹性体）用于制作面部皮肤（可选）。
工具
3D 打印机
螺丝刀、钳子等基础手工工具
电烙铁和焊锡（用于焊接电路）
电脑（用于编程和设计）
软件需求
开发环境：
Arduino IDE (用于为 Arduino 编程)
Python 3.x (用于在 Banana Pi BPI-F3/Raspberry Pi 4上运行高级控制逻辑或上位机程序)

Embodied Perception Head (Embodied perception head)
Project Introduction
Welcome to the open-source Bionic Human Head project! This is an open-source project dedicated to designing and building highly realistic and interactive bionic human heads. Our goal is to create a platform that enables enthusiasts, students and researchers to explore the cutting-edge technologies in robotics, artificial intelligence and human-computer interaction.
Main features
Highly realistic appearance: Utilizing 3D printing technology and meticulous external processing, it creates a lifelike facial look.
Rich expression simulation: Through multi-servo drive, it realizes a variety of complex facial expressions including smiling, frowning, surprise, anger, etc.
Dynamic eye movements: Independently controlled eye rotation and blinking functions enhance the vividness of interaction.
Modular design: Both hardware and software adopt a modular architecture, facilitating assembly, debugging, maintenance, and functional expansion.
Completely open source: All design files (3D models, circuit diagrams) and source codes are freely accessible, encouraging community contributions and secondary development.
Hardware requirements
Electronic components
Microcontroller: It is recommended to use Banana Pi BPI-F3/Raspberry Pi 4 as the main controller.
Servo Motors
Nineteen standard servos (such as the SG90) are used to control facial expressions.
Two high-precision servos (such as MG996R) are used to control the eyes and neck.
Power module
A 5V DC power adapter.
A servo driver board (such as PCA9685) is used to expand the PWM output channel.
Sensor (optional) :
Camera module for visual input.
Microphone module for speech recognition.
Structural components
3D-printed head skeleton, panel and shell.
Hardware parts such as screws, nuts and bearings used for connection and fixation.
Elastic materials (such as silicone and thermoplastic elastomers) are used to make facial skin (optional).
Tools
3D printer
Basic hand tools such as screwdrivers and pliers
Soldering iron and solder (for soldering circuits)
Computer (for programming and design
Software requirements
Development environment
Arduino IDE (for programming Arduino)
Python 3.x (for running advanced control logic or host computer programs on Banana Pi BPI-F3/Raspberry Pi 4)
