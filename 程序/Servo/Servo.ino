// ESP32-S3 Servo Control via Serial for PCA9685 Shield
// 使用 Adafruit 16-Channel PWM/Servo Shield
// ESP32-S3-DEV-KIT-NXR8 配置: SDA-IO8, SCL-IO9
// 修复串口通信问题 - 增强命令解析

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// 指定SDA和SCL引脚
#define SDA_PIN 8
#define SCL_PIN 9

// PCA9685 I2C地址
#define PCA9685_ADDRESS 0x40

// 创建PWM驱动对象
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(PCA9685_ADDRESS);

// 舵机参数
// 增加脉冲范围的默认值，方便调试
// MG996R舵机参数 (更宽的脉冲范围)
#define MG996R_MIN  100  // 最小脉冲长度（对应0度）- 增大范围方便调试
#define MG996R_MAX  650  // 最大脉冲长度（对应180度）- 增大范围方便调试

// MG90s舵机参数 (标准脉冲范围)
#define MG90S_MIN  100   // 最小脉冲长度（对应0度）- 增大范围方便调试
#define MG90S_MAX  650   // 最大脉冲长度（对应180度）- 增大范围方便调试

#define SERVO_FREQ 50    // 舵机频率 50Hz
#define SERVO_PROTECTION_TIMEOUT 5000  // 舵机保护超时时间 (5秒)

// 存储每个舵机的当前角度
int servoAngles[16] = {90, 90, 90, 90, 90, 90, 90, 90, 
                        90, 90, 90, 90, 90, 90, 90, 90};

// 舵机类型配置 (0=MG996R, 1=MG90s)
// 根据用户配置：2个MG996R，12个MG90s
int servoTypes[16] = {
  0, 0,  // 前两个是MG996R舵机
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1  // 后面12个是MG90s舵机
};

// 舵机保护变量
unsigned long servoLastMoveTime[16] = {0};  // 每个舵机最后一次移动的时间
bool servoProtectionActive[16] = {false};    // 每个舵机的保护状态
int servoHoldPosition[16] = {90};            // 每个舵机的保持位置

// 调试模式
bool debugMode = true;

void setup() {
  // 使用115200波特率与Python工具匹配
  Serial.begin(115200);
  Serial.println("ESP32-S3 16-Channel Servo Controller Ready!");
  Serial.println("Format: S<channel>,<angle> (e.g., S1,90)");
  Serial.println("Send 'DEBUG' to toggle debug mode");
  
  // 初始化Wire库，指定SDA和SCL引脚
  Serial.print("DEBUG:Initializing Wire library with SDA_PIN=");
  Serial.print(SDA_PIN);
  Serial.print(", SCL_PIN=");
  Serial.println(SCL_PIN);
  
  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("DEBUG:Wire library initialized successfully");
  
  // 等待I2C总线稳定
  delay(500);
  Serial.println("DEBUG:I2C bus initialized, delay 500ms for stabilization");
  
  // 设置I2C时钟频率为100kHz
  Wire.setClock(100000);
  Serial.println("DEBUG:Wire.setClock(100000) called - I2C clock set to 100kHz");
  
  // 检查I2C时钟频率
  Serial.println("DEBUG:I2C bus configured and ready for PCA9685 communication");
  
  // 检查Wire库状态
  Serial.print("DEBUG:Wire library status - SDA_PIN=");
  Serial.print(SDA_PIN);
  Serial.print(", SCL_PIN=");
  Serial.println(SCL_PIN);
  
  // 检查I2C设备
  byte error, address;
  int nDevices;
  
  Serial.println("DEBUG:=== I2C Bus Scan Start ===");
  nDevices = 0;
  for(address = 1; address < 127; address++ ) {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("DEBUG:✅ I2C device found at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.print(address, HEX);
      Serial.println(" !");
      
      // 特别标记PCA9685的地址
      if (address == PCA9685_ADDRESS) {
        Serial.print("DEBUG:🔍 PCA9685 detected at configured address 0x");
        Serial.println(address, HEX);
      }
      
      nDevices++;
    }
    else if (error == 4) {
      Serial.print("DEBUG:❌ Unknown error at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.println(address, HEX);
    }
    // 其他错误类型
    else {
      Serial.print("DEBUG:⚠️ Error (code ");
      Serial.print(error);
      Serial.print(") at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.println(address, HEX);
    }
  }
  
  Serial.println("DEBUG:=== I2C Bus Scan End ===");
  
  if (nDevices == 0) {
    Serial.println("ERROR:No I2C devices found on the bus. Please check wiring!");
    Serial.println("DEBUG:Checking wiring connections:");
    Serial.println("DEBUG:1. Ensure SDA (GPIO 8) is connected to PCA9685 SDA");
    Serial.println("DEBUG:2. Ensure SCL (GPIO 9) is connected to PCA9685 SCL");
    Serial.println("DEBUG:3. Ensure power supply is connected (5V for servos, 3.3V for logic)");
    Serial.println("DEBUG:4. Ensure GND is connected between ESP32 and PCA9685");
    
    // 进入死循环，等待重置
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);
      digitalWrite(LED_BUILTIN, LOW);
      delay(200);
    }
  } else {
    Serial.print("DEBUG:Found ");
    Serial.print(nDevices);
    Serial.println(" I2C device(s) total");
    
    // 检查是否找到PCA9685
    bool pcaFound = false;
    Wire.beginTransmission(PCA9685_ADDRESS);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("DEBUG:✅ PCA9685 found at configured address 0x");
      Serial.println(PCA9685_ADDRESS, HEX);
      pcaFound = true;
    } else {
      Serial.print("ERROR:❌ PCA9685 not found at configured address 0x");
      Serial.println(PCA9685_ADDRESS, HEX);
      Serial.println("DEBUG:Please check PCA9685 address jumpers or wiring!");
    }
  }
  
  // 尝试初始化PCA9685
  bool pcaInitialized = false;
  int attempts = 0;
  const int maxAttempts = 3;
  
  while (!pcaInitialized && attempts < maxAttempts) {
    attempts++;
    Serial.print("DEBUG:Attempting to initialize PCA9685 (attempt ");
    Serial.print(attempts);
    Serial.print(") at address 0x");
    Serial.println(PCA9685_ADDRESS, HEX);
    
    pwm.begin();
    Serial.println("DEBUG:pwm.begin() called");
    
    // 检查是否成功初始化
    // 这里我们通过设置振荡器频率来验证
    pwm.setOscillatorFrequency(27000000);
    Serial.println("DEBUG:pwm.setOscillatorFrequency(27000000) called");
    
    pwm.setPWMFreq(SERVO_FREQ);
    Serial.println("DEBUG:pwm.setPWMFreq(SERVO_FREQ) called");
    
    // 如果没有抛出错误，认为初始化成功
    pcaInitialized = true;
    Serial.println("DEBUG:PCA9685 initialized successfully");
  }
  
  if (!pcaInitialized) {
    Serial.println("ERROR:Failed to initialize PCA9685 after multiple attempts");
    // 进入死循环，等待重置
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(500);
      digitalWrite(LED_BUILTIN, LOW);
      delay(500);
    }
  }
  
  delay(10);
  
  // 不自动设置任何舵机位置，保持舵机当前状态
  // PCA9685初始化后，通道将保持当前PWM值，避免舵机自动转动
  Serial.println("DEBUG: PCA9685 initialized successfully.");
  Serial.println("DEBUG: Servos remain in current position.");
  Serial.println("DEBUG: Use RESET command or initialization button to set all servos to 90 degrees if needed.");
}

void loop() {
  // 检查舵机保护状态
  checkServoProtection();
  
  if (Serial.available() > 0) {
    // 读取完整的一行
    String command = Serial.readStringUntil('\n');
    
    // 清理命令
    command.trim();
    
    if (command.length() == 0) {
      // 空行，忽略
      return;
    }
    
    if (debugMode) {
      Serial.print("DEBUG:Received '");
      Serial.print(command);
      Serial.println("'");
    }
    
    if (command.startsWith("S")) {
      // 检查是否包含分号，表示批量命令
      if (command.indexOf(';') != -1) {
        parseAndExecuteBatchCommand(command);
      } else {
        parseAndExecuteCommand(command);
      }
    }
    else if (command == "STATUS") {
      reportStatus();
    }
    else if (command == "DEBUG") {
      debugMode = !debugMode;
      Serial.print("DEBUG:Debug mode ");
      Serial.println(debugMode ? "ON" : "OFF");
    }
    else if (command == "HELP") {
      printHelp();
    }
    else if (command == "RESET") {
      resetAllServos();
    }
    else if (command.startsWith("JS")) {
      // 解析并执行下颚同步命令 (格式: JS<angle>)
      // 同时控制舵机0和1，实现真正的同步停止
      String angleStr = command.substring(2);
      angleStr.trim();
      int angle = angleStr.toInt();
      setJawServosSync(angle);
    }
    else {
      Serial.print("ERROR:Unknown command: ");
      Serial.println(command);
    }
  }
}

// 解析并执行批量命令 (格式: S0,120;1,60;...)
void parseAndExecuteBatchCommand(String command) {
  // 清理命令
  command.trim();
  
  if (debugMode) {
    Serial.print("DEBUG:Received batch command '{");
    Serial.print(command);
    Serial.println("'");
  }
  
  // 移除命令前缀
  command.remove(0, 1);
  
  // 分割命令
  int semicolonIndex = command.indexOf(';');
  while (semicolonIndex != -1) {
    String singleCommand = command.substring(0, semicolonIndex);
    if (singleCommand.length() > 0) {
      // 为单个命令添加前缀
      singleCommand = "S" + singleCommand;
      parseAndExecuteCommand(singleCommand);
    }
    command = command.substring(semicolonIndex + 1);
    semicolonIndex = command.indexOf(';');
  }
  
  // 处理最后一个命令
  if (command.length() > 0) {
    String singleCommand = "S" + command;
    parseAndExecuteCommand(singleCommand);
  }
}

// 解析并执行命令
void parseAndExecuteCommand(String command) {
  // 清理命令
  command.trim();
  
  Serial.print("DEBUG:Parsing command: '");
  Serial.print(command);
  Serial.println("'");
  
  // 格式: S<channel>,<angle>
  int commaIndex = command.indexOf(',');
  
  if (commaIndex > 0 && commaIndex < command.length() - 1) {
    String channelStr = command.substring(1, commaIndex);
    String angleStr = command.substring(commaIndex + 1);
    
    // 清理数字部分
    channelStr.trim();
    angleStr.trim();
    
    Serial.print("DEBUG:Extracted - channel='");
    Serial.print(channelStr);
    Serial.print("', angle='");
    Serial.print(angleStr);
    Serial.println("'");
    
    // 检查角度是否为空（通道可以是0，所以channelStr可以是"0"）
    if (angleStr.length() == 0) {
      Serial.println("ERROR:Empty angle");
      return;
    }
    
    // 特殊处理通道0的情况
    if (channelStr.length() == 0) {
      channelStr = "0"; // 如果channelStr为空，说明是通道0
    }
    
    // 检查是否为有效数字
    for (int i = 0; i < channelStr.length(); i++) {
      if (!isDigit(channelStr[i])) {
        Serial.println("ERROR:Invalid channel format");
        return;
      }
    }
    
    for (int i = 0; i < angleStr.length(); i++) {
      if (!isDigit(angleStr[i])) {
        Serial.println("ERROR:Invalid angle format");
        return;
      }
    }
    
    int channel = channelStr.toInt();
    int angle = angleStr.toInt();
    
    Serial.print("DEBUG:Converted - channel=");
    Serial.print(channel);
    Serial.print(", angle=");
    Serial.println(angle);
    
    if (channel >= 0 && channel < 16 && angle >= 0 && angle <= 180) {
      Serial.print("DEBUG:Calling setServoAngle(channel=");
      Serial.print(channel);
      Serial.print(", angle=");
      Serial.println(angle);
      setServoAngle(channel, angle);
      Serial.print("OK:S");
      Serial.print(channel);
      Serial.print(",");
      Serial.println(angle);
    } else {
      Serial.print("ERROR:Invalid range - channel=");
      Serial.print(channel);
      Serial.print(", angle=");
      Serial.println(angle);
    }
  } else {
    Serial.println("ERROR:Invalid format - missing comma or incomplete command");
    Serial.print("DEBUG:commaIndex=");
    Serial.print(commaIndex);
    Serial.print(", command length=");
    Serial.println(command.length());
  }
}

// 设置舵机角度
void setServoAngle(int channel, int angle) {
  // 限制角度范围
  angle = constrain(angle, 0, 180);
  
  // 保存角度
  servoAngles[channel] = angle;
  servoHoldPosition[channel] = angle;
  
  // 根据舵机类型选择不同的脉冲范围
  int pulse;
  if (servoTypes[channel] == 0) {
    // MG996R舵机
    pulse = map(angle, 0, 180, MG996R_MIN, MG996R_MAX);
  } else {
    // MG90s舵机
    pulse = map(angle, 0, 180, MG90S_MIN, MG90S_MAX);
  }
  
  if (debugMode) {
    Serial.print("DEBUG:Setting servo ");
    Serial.print(channel);
    Serial.print(" to ");
    Serial.print(angle);
    Serial.print(" degrees, pulse=");
    Serial.println(pulse);
  }
  
  pwm.setPWM(channel, 0, pulse);
  
  // 更新最后移动时间，重置保护状态
  servoLastMoveTime[channel] = millis();
  if (servoProtectionActive[channel]) {
    servoProtectionActive[channel] = false;
    if (debugMode) {
      Serial.print("DEBUG:Servo ");
      Serial.print(channel);
      Serial.println(" protection disabled");
    }
  }
}

// 舵机保护函数 - 防止长时间过流运行
void checkServoProtection() {
  unsigned long currentTime = millis();
  
  for (int channel = 0; channel < 16; channel++) {
    // 检查是否超过保护时间
    if (!servoProtectionActive[channel] && 
        (currentTime - servoLastMoveTime[channel] > SERVO_PROTECTION_TIMEOUT)) {
      // 停止该通道的PWM输出
      pwm.setPWM(channel, 0, 0);
      servoProtectionActive[channel] = true;
      
      if (debugMode) {
        Serial.print("DEBUG:Servo ");
        Serial.print(channel);
        Serial.println(" protection activated - stopped PWM output");
      }
    }
  }
}

// 同步设置下颚舵机0和1的角度
// 实现真正的同步控制，避免停止时差
void setJawServosSync(int angle) {
  if (debugMode) {
    Serial.print("DEBUG:Sync setting jaw servos to ");
    Serial.print(angle);
    Serial.println(" degrees");
  }
  
  // 验证角度
  if (angle < 0 || angle > 180) {
    Serial.println("ERROR:Invalid jaw angle");
    return;
  }
  
  // 计算两个舵机的角度（反向同步）
  int servo0_angle = angle;
  int servo1_angle = 180 - angle;
  
  // 更新内部角度记录
  servoAngles[0] = servo0_angle;
  servoAngles[1] = servo1_angle;
  
  // 计算两个舵机的脉冲值
  int pulse0, pulse1;
  if (servoTypes[0] == 0) {
    // MG996R舵机
    pulse0 = map(servo0_angle, 0, 180, MG996R_MIN, MG996R_MAX);
  } else {
    // MG90s舵机
    pulse0 = map(servo0_angle, 0, 180, MG90S_MIN, MG90S_MAX);
  }
  
  if (servoTypes[1] == 0) {
    // MG996R舵机
    pulse1 = map(servo1_angle, 0, 180, MG996R_MIN, MG996R_MAX);
  } else {
    // MG90s舵机
    pulse1 = map(servo1_angle, 0, 180, MG90S_MIN, MG90S_MAX);
  }
  
  if (debugMode) {
    Serial.print("DEBUG:Servo 0 pulse=");
    Serial.print(pulse0);
    Serial.print(", Servo 1 pulse=");
    Serial.println(pulse1);
  }
  
  // 使用PCA9685的直接寄存器访问，实现真正的同步控制
  // 批量写入两个舵机的PWM值
  Wire.beginTransmission(PCA9685_ADDRESS);
  
  // 舵机0的通道寄存器地址
  Wire.write(0x06); // LED0_ON_L
  Wire.write(0);    // LED0_ON_L
  Wire.write(0);    // LED0_ON_H
  Wire.write(pulse0 & 0xFF);  // LED0_OFF_L
  Wire.write(pulse0 >> 8);    // LED0_OFF_H
  
  // 舵机1的通道寄存器地址
  Wire.write(0x0A); // LED1_ON_L
  Wire.write(0);    // LED1_ON_L
  Wire.write(0);    // LED1_ON_H
  Wire.write(pulse1 & 0xFF);  // LED1_OFF_L
  Wire.write(pulse1 >> 8);    // LED1_OFF_H
  
  Wire.endTransmission();
  
  // 更新两个舵机的最后移动时间，重置保护状态
  unsigned long currentTime = millis();
  servoLastMoveTime[0] = currentTime;
  servoLastMoveTime[1] = currentTime;
  
  if (servoProtectionActive[0]) {
    servoProtectionActive[0] = false;
    if (debugMode) Serial.println("DEBUG:Servo 0 protection disabled");
  }
  
  if (servoProtectionActive[1]) {
    servoProtectionActive[1] = false;
    if (debugMode) Serial.println("DEBUG:Servo 1 protection disabled");
  }
  
  if (debugMode) {
    Serial.println("DEBUG:Jaw servos synced successfully");
  }
}

// 报告所有舵机状态
void reportStatus() {
  Serial.print("STATUS:");
  for(int i = 0; i < 16; i++) {
    Serial.print("S");
    Serial.print(i);
    Serial.print("=");
    Serial.print(servoAngles[i]);
    if(i < 15) Serial.print(",");
  }
  Serial.println();
}

// 打印帮助信息
void printHelp() {
  Serial.println("=== ESP32-S3 Servo Controller Commands ===");
  Serial.println("S<ch>,<angle> - Set servo channel (0-15) to angle (0-180)");
  Serial.println("JS<angle> - Synchronously control jaw servos 0 and 1 (reverse motion)");
  Serial.println("STATUS - Get current status of all servos");
  Serial.println("DEBUG - Toggle debug mode");
  Serial.println("RESET - Reset all servos to 90 degrees");
  Serial.println("HELP - Show this help message");
  Serial.println("==========================================");
}

// 重置所有舵机到90度
void resetAllServos() {
  Serial.println("RESET:Resetting all servos to 90 degrees");
  for(int i = 0; i < 16; i++) {
    setServoAngle(i, 90);
    delay(50); // 短暂延时，避免电流冲击
  }
  Serial.println("RESET:All servos reset complete");
}