# PySpiFlash 中文使用指南

> 💡 **从零开始** | SPI Flash 完整开发指南

## 📋 目录

1. [环境搭建](#-环境搭建) - 从零开始配置开发环境
2. [硬件连接](#-硬件连接) - FTDI 和 Flash 芯片接线
3. [快速开始](#-快速开始) - 三步上手
4. [常用命令](#-常用命令) - 命令行工具和 Python API
5. [使用场景](#-使用场景) - 实际应用示例
6. [常见问题](#-常见问题) - 故障排除

---

## 🛠️ 环境搭建

### 第一步：安装 Python 和 UV

#### Windows 系统

```powershell
# 1. 安装 Python 3.11+ (如果还没安装)
# 从 https://www.python.org/downloads/ 下载安装

# 2. 安装 UV 包管理器
pip install uv

# 3. 验证安装
uv --version
python --version
```

#### Linux/Mac 系统

```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 第二步：安装 USB 驱动（Windows 必需）

#### 为什么需要特殊驱动？

FTDI 设备默认使用 VCP（虚拟串口）驱动，但 PyFTDI 需要 **WinUSB** 或 **libusbK** 驱动。

#### 安装步骤

1. **下载 Zadig**
   - 访问 https://zadig.akeo.ie/
   - 下载 `zadig-2.7.exe` 或更新版本

2. **以管理员身份运行 Zadig**
   ```powershell
   # 右键 -> 以管理员身份运行
   ```

3. **选择设备**
   - 菜单：`Options` → `List All Devices`
   - 下拉列表中选择你的 FTDI 设备
   - 例如：`USB Serial Converter` 或 `FT232H`

4. **选择驱动**
   - 目标驱动选择：**WinUSB** 或 **libusbK**
   - 点击 `Replace Driver` 或 `Install Driver`
   - 等待安装完成（约 10-30 秒）

5. **验证安装**
   ```powershell
   # 打开设备管理器
   devmgmt.msc
   
   # 应该看到：
   # 通用串行总线设备
   #   └── USB Serial Converter (WinUSB)
   ```

#### ⚠️ 常见错误

**错误**：设备仍显示在 `端口 (COM 和 LPT)` 下
- **原因**：驱动未成功替换
- **解决**：重新运行 Zadig，确保选择正确的设备

**错误**：Zadig 看不到设备
- **原因**：未勾选 "List All Devices"
- **解决**：菜单 → Options → 勾选 "List All Devices"

### 第三步：克隆项目并安装依赖

```powershell
# 1. 克隆或下载项目（如果还没有）
git clone https://github.com/eblot/pyspiflash.git
cd pyspiflash

# 2. 创建虚拟环境
uv venv

# 3. 安装依赖
uv pip install pyftdi pyserial pyusb

# 4. 以开发模式安装项目
uv pip install -e .

# 5. 验证安装
uv run python -c "from spiflash.serialflash import SerialFlashManager; print('安装成功！')"
```

### 第四步：测试连接

```powershell
# 1. 插入 FTDI 设备（先不连接 Flash 芯片）
# 2. 运行设备检测
uv run python test_connection.py

# 期望输出：
# ✓ 检测到 1 个 FTDI 设备：
#   设备 1:
#     URL: ftdi://ftdi:232h/1
#     描述: Digilent USB Device
```

#### 如果检测不到设备

```powershell
# 检查 USB 设备列表
uv run python -c "from pyftdi.ftdi import Ftdi; print(Ftdi.list_devices())"

# 应该看到类似输出：
# [(VID:0403, PID:6014, 'Digilent', 'USB Device', '210512180081')]
```

如果仍然检测不到：
1. 检查设备管理器中驱动状态
2. 尝试更换 USB 端口
3. 重新安装驱动
4. 查看 [常见问题](#-常见问题)

### ✅ 环境搭建完成

如果上述步骤都成功，你已经完成环境搭建！接下来进行 [硬件连接](#-硬件连接)。

---

## 📖 常用命令

### 方式一：命令行工具（推荐日常使用）

#### 查看设备信息

```powershell
# 使用写入工具查看
uv run python flash_write_file.py --info

# 或使用读取工具
uv run python flash_read_file.py --info

# 输出示例：
# ✓ 已连接: Winbond W25Q128 16 MiB
#   容量: 16.00 MB (16,777,216 字节)
#   SPI 频率: 30.00 MHz
#   擦除块大小: 4096 字节
```

#### 写入文件

```powershell
# 基本用法：写入到地址 0（自动擦除+验证）
uv run python flash_write_file.py firmware.bin

# 写入到指定地址（十六进制）
uv run python flash_write_file.py config.bin -a 0x10000

# 写入到指定地址（十进制）
uv run python flash_write_file.py data.bin --address 65536

# 跳过验证（更快但不推荐）
uv run python flash_write_file.py file.bin --no-verify

# 查看完整帮助
uv run python flash_write_file.py --help
```

**写入选项说明**：

| 选项           | 简写 | 默认值             | 说明                     |
| -------------- | ---- | ------------------ | ------------------------ |
| `--address`    | `-a` | 0                  | 目标地址（支持 0x 前缀） |
| `--verify`     | -    | 开启               | 写入后自动验证           |
| `--no-verify`  | -    | -                  | 跳过验证（不推荐）       |
| `--erase`      | -    | 开启               | 写入前自动擦除           |
| `--no-erase`   | -    | -                  | 跳过擦除（危险！）       |
| `--chunk-size` | -    | 4096               | 每次写入块大小           |
| `--url`        | `-u` | ftdi://ftdi:232h/1 | FTDI 设备 URL            |
| `--info`       | `-i` | -                  | 只显示设备信息           |

#### 读取文件

```powershell
# 基本用法：从地址 0 读取
uv run python flash_read_file.py output.bin 4096      # 读 4096 字节
uv run python flash_read_file.py output.bin 4K        # 读 4KB
uv run python flash_read_file.py backup.bin 64K       # 读 64KB
uv run python flash_read_file.py full.bin 1M          # 读 1MB

# 从指定地址读取
uv run python flash_read_file.py firmware.bin 64K -a 0x10000
uv run python flash_read_file.py config.bin 4K --address 0x1000

# 强制覆盖已存在的文件
uv run python flash_read_file.py output.bin 1M --force

# 查看完整帮助
uv run python flash_read_file.py --help
```

**读取选项说明**：

| 选项           | 简写 | 默认值             | 说明                     |
| -------------- | ---- | ------------------ | ------------------------ |
| `--address`    | `-a` | 0                  | 起始地址（支持 0x 前缀） |
| `--force`      | `-f` | -                  | 强制覆盖已存在文件       |
| `--chunk-size` | -    | 4096               | 每次读取块大小           |
| `--url`        | `-u` | ftdi://ftdi:232h/1 | FTDI 设备 URL            |
| `--info`       | `-i` | -                  | 只显示设备信息           |

**大小格式支持**：
- 十进制：`4096`, `65536`, `1048576`
- 十六进制：`0x1000`, `0x10000`, `0x100000`
- 带后缀：`4K`, `64K`, `1M`, `16M` (支持 K/M/G)

### 方式二：Python 代码（开发集成）

#### 基本 API 使用

```python
from spiflash.serialflash import SerialFlashManager

# 1. 连接设备
flash = SerialFlashManager.get_flash_device('ftdi://ftdi:232h/1', cs=0)

# 2. 获取设备信息
print(f"设备: {flash}")
print(f"容量: {flash.get_capacity()} 字节")

# 3. 读取数据
data = flash.read(0x0, 256)           # 从地址 0 读 256 字节
hex_data = data.hex()                 # 转换为十六进制字符串
print(f"数据: {hex_data[:64]}...")    # 显示前 32 字节

# 4. 写入数据（必须先擦除！）
flash.unlock()                        # 解锁设备
flash.erase(0x1000, 4096)             # 擦除 4KB（地址必须对齐）
flash.write(0x1000, b"Hello, World!") # 写入数据

# 5. 验证写入
verify_data = flash.read(0x1000, 13)
assert verify_data == b"Hello, World!", "验证失败！"
print("✓ 验证通过")
```

#### 使用命令函数库

```python
# 导入所有便捷函数
from examples.flash_commands import *

# 连接设备（自动检测）
flash = connect()

# 显示设备信息
info(flash)

# 读取并以十六进制显示
read_hex(flash, 0x0, 256)

# 擦除 4KB 扇区
erase_4k(flash, 0x1000)

# 写入文本
write_text(flash, 0x1000, "Hello, Flash!")

# 写入二进制数据
write_binary(flash, 0x2000, bytes([0x01, 0x02, 0x03, 0x04]))

# 验证数据
verify(flash, 0x1000, b"Hello, Flash!")

# 读取到文件
read_to_file(flash, 0x1000, 1024, "output.bin")

# 从文件写入
write_from_file(flash, 0x10000, "firmware.bin")
```

**可用的函数**（30+ 个）：

| 类别     | 函数                                    | 说明                 |
| -------- | --------------------------------------- | -------------------- |
| **连接** | `connect(url)`                          | 连接设备             |
|          | `info(flash)`                           | 显示设备信息         |
| **读取** | `read_hex(flash, addr, size)`           | 读取并显示为十六进制 |
|          | `read_text(flash, addr, size)`          | 读取并显示为文本     |
|          | `read_to_file(flash, addr, size, file)` | 读取到文件           |
| **擦除** | `erase_4k(flash, addr)`                 | 擦除 4KB             |
|          | `erase_64k(flash, addr)`                | 擦除 64KB            |
|          | `erase_chip(flash)`                     | 擦除整片（危险！）   |
| **写入** | `write_text(flash, addr, text)`         | 写入文本             |
|          | `write_binary(flash, addr, data)`       | 写入二进制           |
|          | `write_from_file(flash, addr, file)`    | 从文件写入           |
| **验证** | `verify(flash, addr, data)`             | 验证数据             |
|          | `compare_files(file1, file2)`           | 比较两个文件         |

查看完整函数列表：

```powershell
uv run python -c "from examples.flash_commands import *; help()"
```

### 方式三：交互式使用（调试测试）

```powershell
# 启动 Python 交互式环境
uv run python

# 然后输入以下命令：
```

```python
>>> from examples.flash_commands import *
>>> 
>>> # 连接设备
>>> flash = connect()
✓ 已连接: Winbond W25Q128 16 MiB

>>> # 查看信息
>>> info(flash)
容量: 16.00 MB (16,777,216 字节)
SPI 频率: 30.00 MHz
擦除块: 4096 字节

>>> # 读取前 256 字节
>>> read_hex(flash, 0x0, 256)
00000000: FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  ................
...

>>> # 写入测试
>>> erase_4k(flash, 0x10000)
✓ 已擦除 4096 字节 @ 0x00010000

>>> write_text(flash, 0x10000, "测试数据 Test Data")
✓ 已写入 23 字节

>>> # 读回验证
>>> read_text(flash, 0x10000, 30)
测试数据 Test Data

>>> # 退出
>>> exit()
```

---

## 🔌 硬件连接

### 准备材料

- ✅ FTDI USB-SPI 桥接器（FT232H、FT2232H 等）
- ✅ SPI Flash 芯片（如 W25Q128、MX25L 等）
- ✅ 杜邦线或面包板
- ✅ 万用表（可选，用于检查连接）

### 引脚对应关系

#### FTDI FT232H → SPI Flash 标准连接

```
FT232H 引脚    功能      SPI Flash 引脚    说明
-----------    ------    --------------    --------------------
AD0 (SCK)      时钟   →  SCK/CLK          串行时钟
AD1 (MOSI)     主出   →  MOSI/DI/SI       主设备输出
AD2 (MISO)     主入   →  MISO/DO/SO       主设备输入
AD3 (CS)       片选   →  CS#/SS#          芯片选择（低电平有效）
GND            地     →  GND/VSS          地线
3.3V/5V        电源   →  VCC/VDD          电源（根据芯片规格）
```

### 接线图示

```
    FTDI FT232H                    SPI Flash (W25Q128)
    ┌──────────┐                   ┌──────────┐
    │          │                   │          │
    │  AD0 ●───┼───────────────────┼──● SCK   │
    │  AD1 ●───┼───────────────────┼──● DI    │
    │  AD2 ●───┼───────────────────┼──● DO    │
    │  AD3 ●───┼───────────────────┼──● CS#   │
    │  GND ●───┼───────────────────┼──● GND   │
    │  3V3 ●───┼───────────────────┼──● VCC   │
    │          │                   │          │
    └──────────┘                   └──────────┘
```

### ⚠️ 重要注意事项

#### 1. 电压匹配

大多数 SPI Flash 使用 **3.3V** 供电，接错电压会**永久损坏芯片**！

```powershell
# 检查芯片数据手册
# 常见电压：
# - W25Q 系列：3.3V (2.7V - 3.6V)
# - MX25L 系列：3.3V (2.7V - 3.6V)
# - AT45 系列：3.3V (2.5V - 3.6V)
```

#### 2. 上拉电阻（推荐）

CS# 引脚建议添加 **10kΩ 上拉电阻**到 VCC，防止启动时误触发。

```
VCC (3.3V)
    │
   [10kΩ]  ← 上拉电阻
    │
    ├─────→ CS# (Flash)
    │
    └─────→ AD3 (FT232H)
```

#### 3. 线材要求

- ✅ 使用**短线**（< 15cm），减少信号干扰
- ✅ MISO/MOSI/SCK 最好使用**双绞线**
- ✅ GND 线要**可靠连接**
- ❌ 避免使用过长或劣质杜邦线

#### 4. 连接检查

使用万用表检查（上电前）：

```powershell
# 1. 检查 VCC 和 GND 之间电阻
#    应该 > 1MΩ（防止短路）

# 2. 检查每个信号线连接
#    确保没有虚接

# 3. 上电后测量 VCC 电压
#    应该在 3.3V ± 0.1V 范围内
```

### 连接示例照片说明

**典型连接方式**：
1. FTDI 插入电脑 USB 口
2. Flash 芯片插在面包板上
3. 用杜邦线连接对应引脚
4. 确保 GND 优先连接

### ✅ 硬件连接完成

连接完成后，运行检测脚本：

```powershell
uv run python test_connection.py
```

如果连接正确，应该看到：

```
✓ 检测到 1 个 FTDI 设备
✓ 已连接: Winbond W25Q128 16 MiB
  容量: 16.00 MB (16,777,216 字节)
  SPI 频率: 30.00 MHz
  擦除块大小: 4096 字节
```

---

## 🎯 快速开始

环境和硬件都准备好后，开始实际操作：

### 1️⃣ 检测设备

```powershell
# 运行设备检测脚本
uv run python test_connection.py

# 或查看设备信息
uv run python flash_write_file.py --info
```

### 2️⃣ 创建测试文件

```powershell
# 使用 Python 生成测试文件
uv run python -c "from examples.flash_commands import create_test_file; create_test_file('test.bin', 64*1024)"

# 或直接运行快速演示（包含自动测试）
uv run python examples\flash_commands.py
```

### 3️⃣ 写入文件到 Flash

```powershell
# 写入到地址 0（会自动擦除和验证）
uv run python flash_write_file.py test_large.bin

# 或写入到指定地址
uv run python flash_write_file.py test_large.bin -a 0x10000
```

**写入过程**：
```
[1/5] 读取文件: test_large.bin
  ✓ 文件大小: 128.00 KB (131072 字节)

[2/5] 解锁设备...
  ✓ 设备已解锁

[3/5] 擦除 Flash...
  进度: [████████████████████] 100.0%
  ✓ 擦除完成 (6.99 秒, 18.30 KB/s)

[4/5] 写入数据...
  进度: [████████████████████] 100.0%
  ✓ 写入完成 (1.29 秒, 99.34 KB/s)

[5/5] 验证数据...
  进度: [████████████████████] 100.0%
  ✓ 验证通过！数据完全匹配
```

### 4️⃣ 读取数据验证

```powershell
# 从 Flash 读取数据
uv run python flash_read_file.py readback.bin 128K -a 0x10000

# 比对文件内容
uv run python -c "import hashlib; orig=open('test_large.bin','rb').read(); back=open('readback.bin','rb').read(); print('MD5 匹配:', hashlib.md5(orig).hexdigest()==hashlib.md5(back).hexdigest())"
```

### 5️⃣ 运行完整示例（学习用）

```powershell
# 运行快速演示脚本（5步自动测试）
uv run python examples\flash_commands.py
```

这个脚本会演示：
- ✓ 连接设备
- ✓ 显示设备信息
- ✓ 读取数据
- ✓ 擦除和写入测试
- ✓ 验证操作结果

---

## 💡 使用场景

### 烧录固件

```powershell
# 引导程序（地址 0）
flash_write_file.py bootloader.bin -a 0x0

# 应用程序（64KB 偏移）
flash_write_file.py application.bin -a 0x10000

# 配置数据（1MB 偏移）
flash_write_file.py config.bin -a 0x100000
```

### 备份和恢复

```powershell
# 完整备份（16MB 芯片）
flash_read_file.py backup.bin 16M

# 恢复备份
flash_write_file.py backup.bin
```

### 部分更新

```powershell
# 只更新配置区（不影响固件）
flash_write_file.py new_config.bin -a 0x1000
```

---

## ⚠️ 重要提示

### 写入规则

1. **必须先擦除再写入**
   - Flash 只能从 `1` 变成 `0`
   - 擦除会将所有位变为 `1` (0xFF)

2. **地址对齐**
   - 4KB 擦除: 地址必须是 `0x1000` 的倍数
   - 64KB 擦除: 地址必须是 `0x10000` 的倍数

3. **验证很重要**
   - 写入工具默认开启验证
   - 不建议使用 `--no-verify`

### 安全建议

```powershell
# ✓ 推荐: 先备份重要数据
flash_read_file.py backup.bin 1M
flash_write_file.py new_firmware.bin

# ✗ 危险: 直接擦除整片
flash.erase(0, -1)  # 不要这样做！
```

---

## 📚 项目文件

```
pyspiflash/
├── flash_write_file.py    # 写入工具（推荐）
├── flash_read_file.py     # 读取工具（推荐）
├── test_connection.py     # 设备检测
├── examples/
│   └── flash_commands.py      # 函数库+快速演示
└── README_CN.md           # 本文档
```

### 详细文档（需要时查看）

- **COMMAND_REFERENCE.md** - 完整 API 参考手册（500+ 行）
- **FLASH_TOOLS_GUIDE.md** - 工具详细说明
- **QUICKSTART.md** - 英文快速指南
- **README.rst** - 官方文档

---

## 🔧 常见问题

### 问题 1: 检测不到设备

**检查**:
```powershell
# 查看设备管理器
devmgmt.msc

# 应该看到:
通用串行总线设备
  └── USB Serial Converter (WinUSB/libusbK)
```

**错误情况**:
```
端口 (COM 和 LPT)
  └── USB Serial Port (COM3)  # ✗ VCP 驱动，需要用 Zadig 替换
```

### 问题 2: "Unable to read JEDEC Id"

**原因**:
- 硬件连接问题
- 电源不足
- 芯片未上电

**解决**:
- 检查连接线是否插好
- 确认芯片供电（用万用表测 VCC）
- 使用短线减少干扰

### 问题 3: 写入验证失败

**原因**:
- 未擦除目标区域
- 硬件连接不稳定

**解决**:
```powershell
# 确保自动擦除开启（默认）
flash_write_file.py file.bin  # ✓ 正确

# 不要跳过擦除
flash_write_file.py file.bin --no-erase  # ✗ 危险
```

---

## 📊 支持的芯片

| 厂商     | 型号  | 容量     | 读速度    | 写速度   |
| -------- | ----- | -------- | --------- | -------- |
| Winbond  | W25Q  | 2-16 MiB | 1.25 MB/s | 63 KB/s  |
| Macronix | MX25L | 2-16 MiB | 1.33 MB/s | 71 KB/s  |
| Micron   | N25Q  | 8 MiB    | 1.31 MB/s | 107 KB/s |
| Atmel    | AT45  | 2-4 MiB  | 1.28 MB/s | 56 KB/s  |

更多型号请参考 `README.rst`

---

## 🆘 获取帮助

### 查看示例

```powershell
# 运行快速演示
uv run python examples\flash_commands.py

# 查看工具帮助
uv run python flash_write_file.py --help
uv run python flash_read_file.py --help
```

### 在线资源

- **PyFTDI 文档**: https://eblot.github.io/pyftdi/
- **项目仓库**: https://github.com/eblot/pyspiflash
- **问题反馈**: https://github.com/eblot/pyspiflash/issues

---

## 🎉 开始使用

```powershell
# 1. 连接 FTDI 设备和 SPI Flash 芯片
# 2. 检测设备
uv run python test_connection.py

# 3. 运行快速演示
uv run python examples\flash_commands.py

# 4. 手动测试 - 生成测试文件
uv run python -c "from examples.flash_commands import create_test_file; create_test_file('test.bin', 64*1024)"

# 5. 写入测试
uv run python flash_write_file.py test.bin -a 0x10000

# 6. 读取验证
uv run python flash_read_file.py readback.bin 64K -a 0x10000
```

**祝你使用愉快！** 🚀
