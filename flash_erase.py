#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
擦除 SPI Flash 指定区域

用法:
    python flash_erase.py <地址> <大小> [选项]

示例:
    python flash_erase.py 0x0 4096              # 擦除前 4KB
    python flash_erase.py 0x10000 0x10000       # 擦除 64KB @ 0x10000
    python flash_erase.py 0x0 -1                # 擦除整个芯片
    python flash_erase.py 0x1000 4k             # 擦除 4KB (支持 k/m 单位)
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


def parse_size(size_str):
    """
    解析大小字符串
    
    支持格式:
        - 十进制: 4096
        - 十六进制: 0x1000
        - 带单位: 4k, 64K, 1M, 16m
        - 整片: -1, all, chip
    """
    size_str = size_str.strip().lower()
    
    # 特殊值: 整片擦除
    if size_str in ['-1', 'all', 'chip', 'full']:
        return -1
    
    # 检查单位
    multiplier = 1
    if size_str.endswith('k'):
        multiplier = 1024
        size_str = size_str[:-1]
    elif size_str.endswith('m'):
        multiplier = 1024 * 1024
        size_str = size_str[:-1]
    
    # 解析数值
    if size_str.startswith('0x'):
        value = int(size_str, 16)
    else:
        value = int(size_str)
    
    return value * multiplier


def parse_address(addr_str):
    """解析地址字符串（支持十进制和十六进制）"""
    addr_str = addr_str.strip()
    if addr_str.startswith('0x') or addr_str.startswith('0X'):
        return int(addr_str, 16)
    else:
        return int(addr_str)


def print_progress_bar(current, total, width=50, prefix=''):
    """打印进度条"""
    if total == 0 or total == -1:
        # 整片擦除无法显示进度
        print(f'\r{prefix}擦除中...', end='', flush=True)
        return
    
    percent = (current / total) * 100
    filled = int(width * current // total)
    bar = '█' * filled + '░' * (width - filled)
    
    print(f'\r{prefix}[{bar}] {percent:.1f}%', end='', flush=True)


def erase_flash(flash, address, size, verify_after=True):
    """
    擦除 Flash 指定区域
    
    参数:
        flash: SPI Flash 设备对象
        address: 起始地址
        size: 擦除大小（-1 表示整片擦除）
        verify_after: 擦除后验证
    """
    print("=" * 70)
    print("SPI Flash 擦除工具")
    print("=" * 70)
    
    flash_capacity = flash.get_capacity()
    block_size = flash.get_erase_size()
    
    # 处理整片擦除
    if size == -1:
        size = flash_capacity
        print(f"\n⚠ 整片擦除模式")
    
    print(f"\n擦除参数:")
    print(f"  起始地址: 0x{address:08X}")
    print(f"  擦除大小: {format_size(size)} ({size:,} 字节)")
    print(f"  结束地址: 0x{(address + size - 1):08X}")
    print(f"  擦除块大小: {block_size} 字节")
    
    # 检查地址对齐
    if address % block_size != 0:
        print(f"\n⚠ 警告: 地址 0x{address:X} 未对齐到 {block_size} 字节边界")
        aligned_address = (address // block_size) * block_size
        print(f"  建议使用对齐地址: 0x{aligned_address:X}")
    
    # 检查容量
    if address + size > flash_capacity:
        raise ValueError(
            f"擦除范围超出芯片容量！"
            f"需要 {format_size(size)}，但从地址 0x{address:X} 到末尾只有 "
            f"{format_size(flash_capacity - address)} 可用"
        )
    
    # 解锁设备
    print(f"\n[1/3] 解锁设备...")
    try:
        flash.unlock()
        print("  ✓ 设备已解锁")
    except Exception as e:
        print(f"  ℹ 解锁信息: {e}")
    
    # 确认操作
    print(f"\n即将擦除 {format_size(size)} ({size:,} 字节)")
    print(f"范围: 0x{address:08X} - 0x{(address + size - 1):08X}")
    
    if size >= 1024 * 1024:  # 1MB 以上需要确认
        response = input("\n⚠ 这是一个大范围擦除操作,确认继续？[Y/n] (直接回车=Yes): ").strip().lower()
        if response and response not in ['y', 'yes']:
            print("已取消操作。")
            return False
    
    # 执行擦除
    print(f"\n[2/3] 擦除中...")
    start_time = time.time()
    
    if size == flash_capacity:
        # 整片擦除
        print("  使用整片擦除命令...")
        flash.erase(0, -1)
        print()  # 换行
    else:
        # 分块擦除以显示进度
        erased = 0
        while erased < size:
            current_address = address + erased
            current_size = min(block_size, size - erased)
            
            flash.erase(current_address, current_size)
            erased += current_size
            
            print_progress_bar(erased, size, prefix='  进度: ')
        print()  # 换行
    
    erase_time = time.time() - start_time
    print(f"  ✓ 擦除完成 (耗时: {format_time(erase_time)})")
    print(f"  ✓ 擦除速度: {format_size(size / erase_time)}/s")
    
    # 验证擦除
    verify_time = 0
    if verify_after:
        print(f"\n[3/3] 验证擦除...")
        print(f"  验证大小: {format_size(size)} ({size:,} 字节)")
        
        start_time = time.time()
        chunk_size = 4096
        verified = 0
        non_erased = 0
        first_error_offset = None
        
        while verified < size:
            current_address = address + verified
            current_size = min(chunk_size, size - verified)
            
            data = flash.read(current_address, current_size)
            
            # 检查是否全为 0xFF
            for i, byte in enumerate(data):
                if byte != 0xFF:
                    if first_error_offset is None:
                        first_error_offset = verified + i
                    non_erased += 1
            
            verified += current_size
            print_progress_bar(verified, size, prefix='  进度: ')
        
        verify_time = time.time() - start_time
        print()  # 换行
        
        if non_erased == 0:
            print(f"  ✓ 验证通过！区域已完全擦除 (耗时: {format_time(verify_time)})")
            print(f"  ✓ 验证速度: {format_size(size / verify_time)}/s")
        else:
            print(f"  ✗ 验证失败！发现 {non_erased} 个字节未擦除")
            if first_error_offset is not None:
                addr = address + first_error_offset
                print(f"  ✗ 第一个非 0xFF 字节在偏移 0x{first_error_offset:X} (地址 0x{addr:X})")
            raise ValueError("擦除验证失败")
    else:
        print(f"\n[3/3] 跳过验证（--no-verify 选项）")
    
    # 总结
    print("\n" + "=" * 70)
    print("✓ 擦除成功！")
    print("=" * 70)
    print(f"地址: 0x{address:08X} - 0x{(address + size - 1):08X}")
    print(f"大小: {format_size(size)} ({size:,} 字节)")
    total_time = erase_time + verify_time
    print(f"总耗时: {format_time(total_time)}")
    print("=" * 70)
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='擦除 SPI Flash 指定区域',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 0x0 4096
      擦除前 4KB (地址 0x0 - 0xFFF)

  %(prog)s 0x10000 64k
      擦除 64KB @ 0x10000

  %(prog)s 0x0 -1
      擦除整个芯片（危险！）

  %(prog)s 0x100000 1m --no-verify
      擦除 1MB 但跳过验证

  %(prog)s 0x1000 4k --url ftdi:///1
      指定 FTDI 设备 URL

大小格式:
  - 十进制: 4096
  - 十六进制: 0x1000
  - 带单位: 4k, 64K, 1M (k=1024, m=1024*1024)
  - 整片: -1, all, chip
        """
    )
    
    parser.add_argument(
        'address',
        type=str,
        help='起始地址（支持十进制或十六进制，如 0x1000）'
    )
    
    parser.add_argument(
        'size',
        type=str,
        help='擦除大小（支持: 4096, 0x1000, 4k, 1m, -1）'
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
        '--verify',
        action='store_true',
        default=True,
        help='擦除后验证（默认已开启）'
    )
    
    parser.add_argument(
        '--no-verify',
        dest='verify',
        action='store_false',
        help='跳过验证（不推荐）'
    )
    
    parser.add_argument(
        '-i', '--info',
        action='store_true',
        help='只显示设备信息，不执行擦除'
    )
    
    args = parser.parse_args()
    
    try:
        # 解析参数
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
        print(f"  擦除块大小: {flash.get_erase_size()} 字节")
        
        # 如果只是查看信息
        if args.info:
            print("\n设备信息显示完成。")
            return 0
        
        # 执行擦除
        erase_flash(flash, address, size, verify_after=args.verify)
        
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
