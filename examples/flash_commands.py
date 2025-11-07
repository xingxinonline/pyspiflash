#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPI Flash 快速命令参考

这个脚本提供了常用的读写擦除命令示例，可以直接在 Python 交互式环境中使用
"""

from spiflash.serialflash import SerialFlashManager, SerialFlash


# ============================================================
# 基础命令
# ============================================================

def connect(url='ftdi://ftdi:232h/1', cs=0):
    """
    连接到 SPI Flash 设备
    
    参数:
        url: FTDI 设备 URL
        cs: 片选引脚编号 (默认 0)
    
    返回:
        flash: SPI Flash 设备对象
    
    示例:
        flash = connect()
        flash = connect('ftdi:///1')
    """
    flash = SerialFlashManager.get_flash_device(url, cs=cs)
    print(f"已连接: {flash}")
    print(f"容量: {flash.get_capacity():,} 字节")
    return flash


def info(flash):
    """
    显示设备信息
    
    示例:
        info(flash)
    """
    print("=" * 60)
    print("设备信息")
    print("=" * 60)
    print(f"设备型号: {flash}")
    print(f"容量: {flash.get_capacity():,} 字节 ({flash.get_capacity()/(1024*1024):.2f} MiB)")
    print(f"SPI 频率: {flash.spi_frequency/1e6:.2f} MHz")
    print(f"擦除块大小: {flash.get_erase_size()} 字节")
    
    print("\n支持的特性:")
    features = [
        ('基本锁定', SerialFlash.FEAT_LOCK),
        ('扇区擦除 (64KB)', SerialFlash.FEAT_SECTERASE),
        ('半扇区擦除 (32KB)', SerialFlash.FEAT_HSECTERASE),
        ('子扇区擦除 (4KB)', SerialFlash.FEAT_SUBSECTERASE),
        ('整片擦除', SerialFlash.FEAT_CHIPERASE),
    ]
    
    for name, feat in features:
        status = "✓" if flash.__class__.has_feature(feat) else "✗"
        print(f"  {status} {name}")


# ============================================================
# 读取命令
# ============================================================

def read_hex(flash, address, length=256):
    """
    读取数据并以十六进制显示
    
    参数:
        flash: SPI Flash 设备对象
        address: 起始地址
        length: 读取长度 (字节)
    
    示例:
        read_hex(flash, 0x0, 256)        # 读取前 256 字节
        read_hex(flash, 0x1000, 128)     # 读取地址 0x1000 的 128 字节
    """
    data = flash.read(address, length)
    print(f"从地址 0x{address:04X} 读取 {length} 字节:")
    print_hex_dump(data, address)
    return data


def read_ascii(flash, address, length=256):
    """
    读取数据并以 ASCII 显示
    
    示例:
        read_ascii(flash, 0x1000, 128)
    """
    data = flash.read(address, length)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
    print(f"从地址 0x{address:04X} 读取 {length} 字节 (ASCII):")
    print(ascii_str)
    return data


def read_bytes(flash, address, length):
    """
    读取原始字节数据
    
    示例:
        data = read_bytes(flash, 0x0, 256)
    """
    return flash.read(address, length)


def dump(flash, address, length, filename):
    """
    将 Flash 内容转储到文件
    
    参数:
        flash: SPI Flash 设备对象
        address: 起始地址
        length: 读取长度
        filename: 输出文件名
    
    示例:
        dump(flash, 0x0, 1024*1024, 'flash_dump.bin')  # 转储 1MB
    """
    print(f"转储 {length:,} 字节到 {filename}...")
    data = flash.read(address, length)
    with open(filename, 'wb') as f:
        f.write(data)
    print(f"✓ 已保存 {len(data):,} 字节")


# ============================================================
# 擦除命令
# ============================================================

def erase_4k(flash, address):
    """
    擦除 4KB 子扇区
    
    参数:
        flash: SPI Flash 设备对象
        address: 扇区起始地址（必须 4KB 对齐）
    
    示例:
        erase_4k(flash, 0x1000)   # 擦除地址 0x1000 的 4KB
        erase_4k(flash, 0x10000)  # 擦除地址 0x10000 的 4KB
    """
    size = 4096
    print(f"擦除 4KB @ 0x{address:05X}...")
    flash.erase(address, size)
    print("✓ 完成")


def erase_64k(flash, address):
    """
    擦除 64KB 扇区
    
    参数:
        address: 扇区起始地址（必须 64KB 对齐）
    
    示例:
        erase_64k(flash, 0x10000)   # 擦除 64KB @ 0x10000
        erase_64k(flash, 0x100000)  # 擦除 64KB @ 0x100000
    """
    size = 65536
    print(f"擦除 64KB @ 0x{address:05X}...")
    flash.erase(address, size)
    print("✓ 完成")


def erase_custom(flash, address, size):
    """
    擦除自定义大小
    
    参数:
        address: 起始地址
        size: 擦除大小（必须对齐到擦除块大小）
    
    示例:
        erase_custom(flash, 0x10000, 8192)    # 擦除 8KB
        erase_custom(flash, 0x20000, 131072)  # 擦除 128KB
    """
    print(f"擦除 {size:,} 字节 @ 0x{address:05X}...")
    flash.erase(address, size)
    print("✓ 完成")


def erase_chip(flash):
    """
    擦除整个芯片（危险！）
    
    警告: 这将清除整个芯片的所有数据！
    
    示例:
        erase_chip(flash)  # 擦除整个芯片
    """
    capacity = flash.get_capacity()
    response = input(f"⚠ 警告：将擦除整个芯片 ({capacity:,} 字节)！确认? (yes/no): ")
    if response.lower() == 'yes':
        print("擦除整个芯片（可能需要几分钟）...")
        flash.erase(0, -1)  # 或 flash.erase(0, capacity)
        print("✓ 完成")
    else:
        print("已取消")


# ============================================================
# 写入命令
# ============================================================

def write_text(flash, address, text):
    """
    写入文本字符串
    
    注意: 写入前必须先擦除目标区域！
    
    参数:
        flash: SPI Flash 设备对象
        address: 写入地址
        text: 文本字符串
    
    示例:
        erase_4k(flash, 0x1000)                    # 先擦除
        write_text(flash, 0x1000, "Hello, World!") # 再写入
    """
    data = text.encode('utf-8')
    print(f"写入 {len(data)} 字节到 0x{address:05X}...")
    flash.write(address, data)
    print("✓ 完成")
    return len(data)


def write_bytes(flash, address, data):
    """
    写入字节数据
    
    参数:
        data: bytes 或 bytearray 对象
    
    示例:
        erase_4k(flash, 0x2000)                          # 先擦除
        write_bytes(flash, 0x2000, b'\x01\x02\x03\x04')  # 写入字节
    """
    print(f"写入 {len(data)} 字节到 0x{address:05X}...")
    flash.write(address, data)
    print("✓ 完成")


def write_file(flash, address, filename):
    """
    从文件写入数据
    
    参数:
        address: 写入地址
        filename: 源文件名
    
    示例:
        # 假设要写入 firmware.bin (64KB)
        erase_64k(flash, 0x0)                      # 先擦除 64KB
        write_file(flash, 0x0, 'firmware.bin')     # 写入文件
    """
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"从 {filename} 写入 {len(data):,} 字节到 0x{address:05X}...")
    flash.write(address, data)
    print("✓ 完成")
    return len(data)


def write_pattern(flash, address, pattern, count):
    """
    写入重复模式
    
    参数:
        pattern: 模式字节序列
        count: 重复次数
    
    示例:
        erase_4k(flash, 0x3000)                           # 先擦除
        write_pattern(flash, 0x3000, b'\xAA\x55', 128)    # 写入 256 字节
    """
    data = pattern * count
    print(f"写入模式 {pattern.hex()} × {count} 到 0x{address:05X}...")
    flash.write(address, data)
    print("✓ 完成")


# ============================================================
# 验证命令
# ============================================================

def verify(flash, address, expected_data):
    """
    验证数据
    
    参数:
        address: 验证地址
        expected_data: 期望的数据
    
    示例:
        write_text(flash, 0x1000, "Test")
        verify(flash, 0x1000, b"Test")
    """
    length = len(expected_data)
    actual_data = flash.read(address, length)
    
    if actual_data == expected_data:
        print(f"✓ 验证通过 @ 0x{address:05X} ({length} 字节)")
        return True
    else:
        print(f"✗ 验证失败 @ 0x{address:05X}")
        for i in range(min(length, len(actual_data))):
            if actual_data[i] != expected_data[i]:
                print(f"  第一个差异在偏移 {i}: 期望 0x{expected_data[i]:02X}, 实际 0x{actual_data[i]:02X}")
                break
        return False


def verify_erased(flash, address, length):
    """
    验证区域已擦除（全为 0xFF）
    
    示例:
        erase_4k(flash, 0x1000)
        verify_erased(flash, 0x1000, 4096)
    """
    data = flash.read(address, length)
    erased_count = sum(1 for b in data if b == 0xFF)
    
    if erased_count == length:
        print(f"✓ 区域已擦除 @ 0x{address:05X} ({length} 字节)")
        return True
    else:
        print(f"✗ 区域未完全擦除 @ 0x{address:05X}")
        print(f"  已擦除: {erased_count}/{length} 字节")
        return False


# ============================================================
# 其他命令
# ============================================================

def unlock(flash):
    """
    解锁设备（移除写保护）
    
    某些芯片出厂时带有写保护，需要先解锁
    
    示例:
        unlock(flash)
    """
    try:
        flash.unlock()
        print("✓ 设备已解锁")
    except Exception as e:
        print(f"解锁信息: {e}")


def is_busy(flash):
    """
    检查设备是否忙碌
    
    示例:
        if is_busy(flash):
            print("设备忙碌中...")
    """
    busy = flash.is_busy()
    print(f"设备状态: {'忙碌' if busy else '空闲'}")
    return busy


# ============================================================
# 辅助函数
# ============================================================

def print_hex_dump(data, address=0, bytes_per_line=16):
    """打印十六进制数据"""
    for i in range(0, len(data), bytes_per_line):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+bytes_per_line])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+bytes_per_line])
        print(f'  {address+i:04X}: {hex_str:<48} {ascii_str}')


# ============================================================
# 使用示例
# ============================================================

if __name__ == '__main__':
    print("=" * 70)
    print("SPI Flash 快速命令参考")
    print("=" * 70)
    print("""
这个脚本提供了常用命令的函数封装，可以在 Python 交互式环境中使用：

1. 启动 Python 交互式环境：
   uv run python

2. 导入命令：
   from examples.flash_commands import *

3. 连接设备：
   flash = connect()

4. 常用操作：
   info(flash)                              # 显示设备信息
   read_hex(flash, 0x0, 256)                # 读取并显示
   erase_4k(flash, 0x1000)                  # 擦除 4KB
   write_text(flash, 0x1000, "Hello!")      # 写入文本
   verify(flash, 0x1000, b"Hello!")         # 验证数据

详细命令请参考脚本中的函数文档。
""")


# ============================================================
# 快速演示和测试工具
# ============================================================

def create_test_file(filename='test_data.bin', size=128*1024):
    """
    创建测试文件（循环 0x00-0xFF 模式）
    
    参数:
        filename: 文件名
        size: 文件大小（字节）
    
    示例:
        create_test_file('test.bin', 64*1024)  # 64KB
    """
    pattern = bytes(range(256))
    data = pattern * (size // 256) + pattern[:size % 256]
    
    with open(filename, 'wb') as f:
        f.write(data)
    
    print(f"✓ 已创建测试文件: {filename} ({size:,} 字节)")
    return filename


def demo():
    """
    运行快速演示（读取设备信息 + 简单读写测试）
    
    示例:
        demo()
    """
    print("=" * 70)
    print("SPI Flash 快速演示")
    print("=" * 70)
    
    # 连接设备
    print("\n[1/5] 连接设备...")
    flash = connect()
    
    # 显示信息
    print("\n[2/5] 设备信息:")
    info(flash)
    
    # 读取测试
    print("\n[3/5] 读取测试 (地址 0x0, 256 字节):")
    read_hex(flash, 0x0, 64)  # 只显示前 64 字节
    print("    ...")
    
    # 写入测试
    print("\n[4/5] 写入测试 (地址 0x10000):")
    test_addr = 0x10000
    test_data = "PySpiFlash Test"
    
    print(f"    擦除 4KB @ 0x{test_addr:05X}...")
    erase_4k(flash, test_addr)
    
    print(f"    写入文本: '{test_data}'")
    write_text(flash, test_addr, test_data)
    
    # 验证
    print("\n[5/5] 验证测试:")
    verify(flash, test_addr, test_data.encode())
    
    print("\n" + "=" * 70)
    print("✓ 演示完成！")
    print("=" * 70)
    print("\n提示: 在 Python 交互式环境中使用更灵活")
    print("     >>> from examples.flash_commands import *")
    print("     >>> flash = connect()")
    print("     >>> help_commands()")


if __name__ == '__main__':
    # 如果直接运行，执行演示
    try:
        demo()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        print("\n请确保:")
        print("  1. FTDI 设备已连接")
        print("  2. WinUSB/libusbK 驱动已安装")
        print("  3. SPI Flash 芯片已正确连接")
