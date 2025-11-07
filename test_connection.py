#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 FTDI 设备连接和 SPI Flash 芯片检测

使用前确保：
1. 已使用 Zadig 安装 WinUSB 驱动
2. FTDI 设备已正确连接
3. SPI Flash 芯片已连接到 FTDI 的 SPI 引脚
"""

import sys


def test_ftdi_devices():
    """列出所有可用的 FTDI 设备"""
    print("=" * 60)
    print("步骤 1: 检测 FTDI 设备")
    print("=" * 60)
    
    try:
        from pyftdi.ftdi import Ftdi
        
        # 列出所有 FTDI 设备（包括 Digilent 等第三方设备）
        # 常见的 FTDI VID:PID 组合
        vps = [
            (0x0403, 0x6001),  # FT232
            (0x0403, 0x6010),  # FT2232
            (0x0403, 0x6011),  # FT4232
            (0x0403, 0x6014),  # FT232H
            (0x0403, 0x6015),  # FT230X
        ]
        devices = Ftdi.find_all(vps=vps, nocache=True)
        
        if not devices:
            print("❌ 未检测到 FTDI 设备！")
            print("\n请检查：")
            print("  1. FTDI 设备是否已连接")
            print("  2. 是否已使用 Zadig 安装 WinUSB 驱动")
            print("  3. 设备管理器中是否显示为 'libusbK' 或 'WinUSB' 设备")
            return False
        
        print(f"✓ 检测到 {len(devices)} 个 FTDI 设备：\n")
        for idx, (device, interface) in enumerate(devices, 1):
            print(f"  设备 {idx}:")
            print(f"    URL: ftdi://{device.bus}:{device.address}/{interface}")
            print(f"    总线: {device.bus}, 地址: {device.address}")
            print(f"    接口: {interface}")
            print(f"    描述: {device.description if hasattr(device, 'description') else 'N/A'}")
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装 pyftdi: uv pip install pyftdi")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_spi_flash(url=None):
    """测试 SPI Flash 芯片连接"""
    print("=" * 60)
    print("步骤 2: 检测 SPI Flash 芯片")
    print("=" * 60)
    
    try:
        from spiflash.serialflash import SerialFlashManager
        
        # 如果没有指定 URL，使用默认值
        if url is None:
            # 尝试常见的 FTDI 设备 URL
            test_urls = [
                'ftdi://ftdi:232h/1',  # FT232H
                'ftdi://ftdi:2232h/1', # FT2232H
                'ftdi://ftdi:4232h/1', # FT4232H
                'ftdi:///1',           # 自动检测第一个设备
            ]
        else:
            test_urls = [url]
        
        flash = None
        working_url = None
        
        for test_url in test_urls:
            print(f"\n尝试连接: {test_url}")
            try:
                flash = SerialFlashManager.get_flash_device(test_url, cs=0)
                working_url = test_url
                print(f"✓ 连接成功！")
                break
            except Exception as e:
                print(f"  失败: {e}")
                continue
        
        if flash is None:
            print("\n❌ 无法连接到 SPI Flash 芯片！")
            print("\n请检查：")
            print("  1. SPI Flash 芯片是否正确连接到 FTDI")
            print("  2. 连接线路（MOSI, MISO, SCK, CS）")
            print("  3. 电源供电是否正常")
            return False
        
        print("\n" + "=" * 60)
        print("SPI Flash 芯片信息")
        print("=" * 60)
        print(f"设备: {flash}")
        capacity = flash.get_capacity()
        print(f"容量: {capacity:,} 字节 ({capacity / (1024*1024):.2f} MiB)")
        print(f"SPI 频率: {flash.spi_frequency / 1e6:.2f} MHz")
        print(f"连接 URL: {working_url}")
        
        # 读取测试
        print("\n" + "=" * 60)
        print("读取测试 (前 256 字节)")
        print("=" * 60)
        try:
            data = flash.read(0, 256)
            print(f"成功读取 {len(data)} 字节")
            
            # 显示前 64 字节的十六进制
            print("\n前 64 字节 (十六进制):")
            for i in range(0, min(64, len(data)), 16):
                hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
            
        except Exception as e:
            print(f"❌ 读取失败: {e}")
            return False
        
        print("\n✓ 所有测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装 pyspiflash: uv pip install -e .")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("PySpiFlash 连接测试工具")
    print("=" * 60 + "\n")
    
    # 步骤 1: 检测 FTDI 设备
    if not test_ftdi_devices():
        sys.exit(1)
    
    # 步骤 2: 检测 SPI Flash
    input("\n按 Enter 继续测试 SPI Flash 芯片...")
    
    # 可以在这里指定特定的 URL，例如：
    # test_spi_flash('ftdi://ftdi:232h/1')
    if not test_spi_flash():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
