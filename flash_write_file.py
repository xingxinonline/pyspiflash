#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将文件写入 SPI Flash 指定地址

用法:
    python flash_write_file.py <文件路径> [选项]

示例:
    python flash_write_file.py firmware.bin
    python flash_write_file.py firmware.bin --address 0x10000
    python flash_write_file.py firmware.bin -a 0x0 --verify
    python flash_write_file.py data.bin -a 0x20000 --no-erase
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


def calculate_erase_size(data_size, block_size=4096):
    """计算需要擦除的大小（向上取整到块大小）"""
    return ((data_size + block_size - 1) // block_size) * block_size


def print_progress_bar(current, total, width=50, prefix=''):
    """打印进度条"""
    if total == 0:
        percent = 100
    else:
        percent = (current / total) * 100
    
    filled = int(width * current // total) if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)
    
    print(f'\r{prefix}[{bar}] {percent:.1f}%', end='', flush=True)


def write_file_to_flash(flash, file_path, address=0, verify=True, erase=True, chunk_size=4096):
    """
    将文件写入 Flash
    
    参数:
        flash: SPI Flash 设备对象
        file_path: 要写入的文件路径
        address: 目标地址（默认 0）
        verify: 是否验证写入（默认 True）
        erase: 是否自动擦除（默认 True）
        chunk_size: 每次写入的块大小（默认 4096）
    """
    print("=" * 70)
    print("SPI Flash 文件写入工具")
    print("=" * 70)
    
    # 读取文件
    print(f"\n[1/5] 读取文件: {file_path}")
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    data_size = len(data)
    print(f"  ✓ 文件大小: {format_size(data_size)} ({data_size:,} 字节)")
    print(f"  ✓ 目标地址: 0x{address:08X}")
    
    # 检查容量
    flash_capacity = flash.get_capacity()
    if address + data_size > flash_capacity:
        raise ValueError(
            f"文件太大！需要 {format_size(data_size)}，"
            f"但从地址 0x{address:X} 到末尾只有 {format_size(flash_capacity - address)} 可用"
        )
    
    # 解锁设备
    print(f"\n[2/5] 解锁设备...")
    try:
        flash.unlock()
        print("  ✓ 设备已解锁")
    except Exception as e:
        print(f"  ℹ 解锁信息: {e}")
    
    # 擦除
    if erase:
        erase_size = calculate_erase_size(data_size, flash.get_erase_size())
        print(f"\n[3/5] 擦除 Flash...")
        print(f"  擦除大小: {format_size(erase_size)} ({erase_size:,} 字节)")
        print(f"  擦除范围: 0x{address:08X} - 0x{(address + erase_size - 1):08X}")
        
        start_time = time.time()
        
        # 分块擦除以显示进度
        block_size = flash.get_erase_size()
        erased = 0
        
        while erased < erase_size:
            current_address = address + erased
            current_size = min(block_size, erase_size - erased)
            
            flash.erase(current_address, current_size)
            erased += current_size
            
            print_progress_bar(erased, erase_size, prefix='  进度: ')
        
        erase_time = time.time() - start_time
        print(f"\n  ✓ 擦除完成 (耗时: {format_time(erase_time)})")
        print(f"  ✓ 擦除速度: {format_size(erase_size / erase_time)}/s")
    else:
        print(f"\n[3/5] 跳过擦除（--no-erase 选项）")
        print("  ⚠ 警告: 未擦除可能导致写入失败或数据错误")
    
    # 写入
    print(f"\n[4/5] 写入数据...")
    print(f"  写入大小: {format_size(data_size)} ({data_size:,} 字节)")
    
    start_time = time.time()
    written = 0
    
    while written < data_size:
        current_address = address + written
        current_size = min(chunk_size, data_size - written)
        current_data = data[written:written + current_size]
        
        flash.write(current_address, current_data)
        written += current_size
        
        print_progress_bar(written, data_size, prefix='  进度: ')
    
    write_time = time.time() - start_time
    print(f"\n  ✓ 写入完成 (耗时: {format_time(write_time)})")
    print(f"  ✓ 写入速度: {format_size(data_size / write_time)}/s")
    
    # 验证
    if verify:
        print(f"\n[5/5] 验证数据...")
        print(f"  验证大小: {format_size(data_size)} ({data_size:,} 字节)")
        
        start_time = time.time()
        verified = 0
        errors = 0
        first_error_offset = None
        
        while verified < data_size:
            current_address = address + verified
            current_size = min(chunk_size, data_size - verified)
            
            readback = flash.read(current_address, current_size)
            expected = data[verified:verified + current_size]
            
            # 检查差异
            for i, (a, b) in enumerate(zip(readback, expected)):
                if a != b:
                    if first_error_offset is None:
                        first_error_offset = verified + i
                    errors += 1
            
            verified += current_size
            print_progress_bar(verified, data_size, prefix='  进度: ')
        
        verify_time = time.time() - start_time
        
        if errors == 0:
            print(f"\n  ✓ 验证通过！数据完全匹配 (耗时: {format_time(verify_time)})")
            print(f"  ✓ 验证速度: {format_size(data_size / verify_time)}/s")
        else:
            print(f"\n  ✗ 验证失败！发现 {errors} 个字节不匹配")
            if first_error_offset is not None:
                print(f"  ✗ 第一个错误在偏移 0x{first_error_offset:X} (地址 0x{address + first_error_offset:X})")
            raise ValueError("数据验证失败")
    else:
        print(f"\n[5/5] 跳过验证（--no-verify 选项）")
    
    # 总结
    print("\n" + "=" * 70)
    print("✓ 写入成功！")
    print("=" * 70)
    print(f"文件: {file_path.name}")
    print(f"大小: {format_size(data_size)} ({data_size:,} 字节)")
    print(f"地址: 0x{address:08X} - 0x{(address + data_size - 1):08X}")
    
    total_time = (erase_time if erase else 0) + write_time + (verify_time if verify else 0)
    print(f"总耗时: {format_time(total_time)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='将文件写入 SPI Flash 指定地址',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s firmware.bin
      将 firmware.bin 写入地址 0x0（默认）

  %(prog)s firmware.bin --address 0x10000
      将文件写入地址 0x10000 (64KB 偏移)

  %(prog)s data.bin -a 0x100000 --verify
      写入到 0x100000 并验证（默认已开启验证）

  %(prog)s bootloader.bin -a 0 --no-verify
      写入到地址 0 但跳过验证（不推荐）

  %(prog)s config.bin -a 0x1000 --no-erase
      写入到 0x1000 但不自动擦除（危险，需手动先擦除）

  %(prog)s backup.bin -a 0x200000 --url ftdi:///1
      指定 FTDI 设备 URL
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',  # 可选参数
        help='要写入的文件路径'
    )
    
    parser.add_argument(
        '-a', '--address',
        type=str,
        default='0',
        help='目标地址（支持十进制或十六进制，如 0x1000）。默认: 0'
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
        help='写入后验证数据（默认已开启）'
    )
    
    parser.add_argument(
        '--no-verify',
        dest='verify',
        action='store_false',
        help='跳过验证（不推荐）'
    )
    
    parser.add_argument(
        '--erase',
        action='store_true',
        default=True,
        help='写入前自动擦除（默认已开启）'
    )
    
    parser.add_argument(
        '--no-erase',
        dest='erase',
        action='store_false',
        help='跳过自动擦除（危险，需确保目标区域已擦除）'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=4096,
        help='每次写入的块大小（字节）。默认: 4096'
    )
    
    parser.add_argument(
        '-i', '--info',
        action='store_true',
        help='只显示设备信息，不执行写入'
    )
    
    args = parser.parse_args()
    
    try:
        # 解析地址
        address = parse_address(args.address)
        
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
        
        # 检查文件参数
        if not args.file:
            print("\n❌ 错误: 需要指定文件路径")
            print("使用 --help 查看帮助信息")
            return 1
        
        # 检查文件
        if not Path(args.file).exists():
            print(f"\n❌ 错误: 文件不存在: {args.file}")
            return 1
        
        # 确认操作
        file_size = Path(args.file).stat().st_size
        print(f"\n即将执行的操作:")
        print(f"  文件: {args.file}")
        print(f"  大小: {format_size(file_size)} ({file_size:,} 字节)")
        print(f"  目标地址: 0x{address:08X}")
        print(f"  自动擦除: {'是' if args.erase else '否'}")
        print(f"  验证: {'是' if args.verify else '否'}")
        
        response = input("\n确认开始写入？(yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("已取消操作。")
            return 0
        
        # 执行写入
        write_file_to_flash(
            flash,
            args.file,
            address=address,
            verify=args.verify,
            erase=args.erase,
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
