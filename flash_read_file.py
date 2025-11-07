#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 SPI Flash 指定地址读取数据到文件

用法:
    python flash_read_file.py <输出文件> <大小> [选项]

示例:
    python flash_read_file.py dump.bin 4096
    python flash_read_file.py firmware.bin 65536 --address 0x10000
    python flash_read_file.py backup.bin 1048576 -a 0x0
"""

import sys
import argparse
import time
from pathlib import Path
from spiflash.serialflash import SerialFlashManager


def format_size(size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} GB"


def format_time(seconds):
    """格式化时间"""
    if seconds < 60:
        return f"{seconds:.2f} 秒"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes} 分 {secs:.1f} 秒"


def parse_address(addr_str):
    """解析地址字符串（支持十进制和十六进制）"""
    addr_str = addr_str.strip()
    if addr_str.startswith('0x') or addr_str.startswith('0X'):
        return int(addr_str, 16)
    else:
        return int(addr_str)


def parse_size(size_str):
    """解析大小字符串（支持 K, M, G 后缀）"""
    size_str = size_str.strip().upper()
    
    multipliers = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            return int(float(size_str[:-1]) * multiplier)
    
    # 支持十六进制
    if size_str.startswith('0X'):
        return int(size_str, 16)
    
    return int(size_str)


def print_progress_bar(current, total, width=50, prefix=''):
    """打印进度条"""
    if total == 0:
        percent = 100
    else:
        percent = (current / total) * 100
    
    filled = int(width * current // total) if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)
    
    print(f'\r{prefix}[{bar}] {percent:.1f}%', end='', flush=True)


def read_flash_to_file(flash, output_file, size, address=0, chunk_size=4096):
    """
    从 Flash 读取数据到文件
    
    参数:
        flash: SPI Flash 设备对象
        output_file: 输出文件路径
        size: 读取大小（字节）
        address: 起始地址（默认 0）
        chunk_size: 每次读取的块大小（默认 4096）
    """
    print("=" * 70)
    print("SPI Flash 文件读取工具")
    print("=" * 70)
    
    # 检查参数
    print(f"\n[1/3] 检查参数...")
    print(f"  ✓ 起始地址: 0x{address:08X}")
    print(f"  ✓ 读取大小: {format_size(size)} ({size:,} 字节)")
    print(f"  ✓ 输出文件: {output_file}")
    
    # 检查容量
    flash_capacity = flash.get_capacity()
    if address + size > flash_capacity:
        raise ValueError(
            f"读取范围超出容量！需要 {format_size(size)}，"
            f"但从地址 0x{address:X} 到末尾只有 {format_size(flash_capacity - address)} 可用"
        )
    
    # 读取数据
    print(f"\n[2/3] 从 Flash 读取数据...")
    print(f"  读取范围: 0x{address:08X} - 0x{(address + size - 1):08X}")
    
    start_time = time.time()
    data = bytearray()
    read_bytes = 0
    
    while read_bytes < size:
        current_address = address + read_bytes
        current_size = min(chunk_size, size - read_bytes)
        
        chunk = flash.read(current_address, current_size)
        data.extend(chunk)
        read_bytes += len(chunk)
        
        print_progress_bar(read_bytes, size, prefix='  进度: ')
    
    read_time = time.time() - start_time
    print(f"\n  ✓ 读取完成 (耗时: {format_time(read_time)})")
    print(f"  ✓ 读取速度: {format_size(size / read_time)}/s")
    
    # 保存到文件
    print(f"\n[3/3] 保存到文件...")
    output_path = Path(output_file)
    
    # 检查文件是否存在
    if output_path.exists():
        response = input(f"  ⚠ 文件 {output_file} 已存在，是否覆盖？(yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("  已取消保存。")
            return
    
    # 创建目录（如果需要）
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(data)
    
    actual_size = output_path.stat().st_size
    print(f"  ✓ 已保存 {format_size(actual_size)} ({actual_size:,} 字节)")
    
    # 总结
    print("\n" + "=" * 70)
    print("✓ 读取成功！")
    print("=" * 70)
    print(f"源地址: 0x{address:08X} - 0x{(address + size - 1):08X}")
    print(f"文件: {output_path.absolute()}")
    print(f"大小: {format_size(size)} ({size:,} 字节)")
    print(f"总耗时: {format_time(read_time)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='从 SPI Flash 指定地址读取数据到文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s dump.bin 4096
      从地址 0x0 读取 4KB 到 dump.bin

  %(prog)s firmware.bin 64K --address 0x10000
      从地址 0x10000 读取 64KB（支持 K 后缀）

  %(prog)s backup.bin 1M -a 0x0
      从地址 0x0 读取 1MB（支持 M 后缀）

  %(prog)s full.bin 0x1000000 -a 0
      读取 16MB（支持十六进制）

  %(prog)s config.bin 256 -a 0x1000 --url ftdi:///1
      指定 FTDI 设备 URL
        """
    )
    
    parser.add_argument(
        'output',
        help='输出文件路径'
    )
    
    parser.add_argument(
        'size',
        type=str,
        help='读取大小（字节），支持 K/M/G 后缀，如: 4096, 64K, 1M'
    )
    
    parser.add_argument(
        '-a', '--address',
        type=str,
        default='0',
        help='起始地址（支持十进制或十六进制，如 0x1000）。默认: 0'
    )
    
    parser.add_argument(
        '-u', '--url',
        type=str,
        default='ftdi://ftdi:232h/1',
        help='FTDI 设备 URL。默认: ftdi://ftdi:232h/1'
    )
    
    parser.add_argument(
        '-c', '--cs',
        type=int,
        default=0,
        help='SPI 片选引脚编号。默认: 0'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=4096,
        help='每次读取的块大小（字节）。默认: 4096'
    )
    
    parser.add_argument(
        '-i', '--info',
        action='store_true',
        help='只显示设备信息，不执行读取'
    )
    
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='强制覆盖已存在的文件'
    )
    
    args = parser.parse_args()
    
    try:
        # 解析地址和大小
        address = parse_address(args.address)
        size = parse_size(args.size)
        
        # 连接设备
        print(f"连接 SPI Flash 设备...")
        print(f"  URL: {args.url}")
        print(f"  CS: {args.cs}")
        
        flash = SerialFlashManager.get_flash_device(args.url, cs=args.cs)
        
        print(f"\n✓ 已连接: {flash}")
        print(f"  容量: {format_size(flash.get_capacity())} ({flash.get_capacity():,} 字节)")
        print(f"  SPI 频率: {flash.spi_frequency / 1e6:.2f} MHz")
        
        # 如果只是查看信息
        if args.info:
            print("\n设备信息显示完成。")
            return 0
        
        # 检查文件冲突
        output_path = Path(args.output)
        if output_path.exists() and not args.force:
            response = input(f"\n⚠ 文件 {args.output} 已存在，是否覆盖？(yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("已取消操作。")
                return 0
        
        # 确认操作
        print(f"\n即将执行的操作:")
        print(f"  起始地址: 0x{address:08X}")
        print(f"  读取大小: {format_size(size)} ({size:,} 字节)")
        print(f"  输出文件: {args.output}")
        
        if not args.force:
            response = input("\n确认开始读取？(yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("已取消操作。")
                return 0
        
        # 执行读取
        read_flash_to_file(
            flash,
            args.output,
            size,
            address=address,
            chunk_size=args.chunk_size
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断操作")
        return 130
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
