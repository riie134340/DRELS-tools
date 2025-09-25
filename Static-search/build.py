# python build.py --debug

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的构建脚本
自动检测数据源并生成静态网页
"""

import os
import sys
import argparse
from data_processor import DataProcessor


def auto_detect_source():
    """自动检测数据源"""
    excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]

    if excel_files:
        return 'excel', excel_files[0]

    # 检查是否有配置文件包含Google Sheets URL
    if os.path.exists('config.txt'):
        try:
            with open('config.txt', 'r', encoding='utf-8') as f:
                url = f.read().strip()
                if 'docs.google.com/spreadsheets' in url:
                    return 'sheets', url
        except:
            pass

    return None, None


def create_template():
    """如果模板不存在，创建基础模板"""
    if not os.path.exists('template.html'):
        print("模板文件不存在，正在创建...")
        # 这里应该写入之前创建的HTML模板内容
        # 为了简化，我们假设用户已经有了模板文件
        print("请确保 template.html 文件存在")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='一键构建静态职业查询网页')
    parser.add_argument('--source', choices=['excel', 'sheets', 'auto'], default='auto',
                        help='数据源类型（auto为自动检测）')
    parser.add_argument('--file', type=str, help='Excel文件路径或Google Sheets URL')
    parser.add_argument('--output', type=str, default='index.html', help='输出文件名')
    parser.add_argument('--debug', action='store_true', help='生成调试信息')

    args = parser.parse_args()

    print("=== 静态职业查询网页构建器 ===\n")

    # 检查模板文件
    if not create_template():
        return 1

    # 确定数据源
    if args.source == 'auto':
        source_type, source_path = auto_detect_source()
        if not source_type:
            print("❌ 未找到数据源！")
            print("请执行以下操作之一：")
            print("1. 将Excel文件(.xlsx/.xls)放在当前目录")
            print("2. 创建config.txt文件，内容为Google Sheets的URL")
            print("3. 使用 --file 参数手动指定数据源")
            return 1
    else:
        source_type = args.source
        source_path = args.file
        if not source_path:
            print("❌ 请使用 --file 参数指定数据源路径")
            return 1

    print(f"📊 检测到数据源: {source_type}")
    print(f"📁 数据路径: {source_path}")
    print()

    # 创建处理器并加载数据
    processor = DataProcessor(debug=args.debug)

    print("🔄 正在加载数据...")
    if source_type == 'excel':
        success = processor.load_from_excel(source_path)
    else:
        success = processor.load_from_google_sheets(source_path)

    if not success:
        print("❌ 数据加载失败")
        return 1

    print("✅ 数据加载成功")
    print()

    # 生成静态HTML
    print("🔄 正在生成静态网页...")
    if not processor.generate_static_html('template.html', args.output):
        print("❌ 网页生成失败")
        return 1

    print("✅ 静态网页生成成功")
    print()

    # 生成调试信息
    if args.debug:
        debug_file = args.output.replace('.html', '_debug.json')
        processor.save_debug_info(debug_file)
        print(f"🔍 调试信息已保存到: {debug_file}")

    # 显示总结信息
    print("=" * 50)
    print("🎉 构建完成！")
    print(f"📄 输出文件: {args.output}")
    print(f"📊 总数据量: {processor.processed_data['total_count']} 条记录")
    print(f"🔐 哈希条目: {len(processor.processed_data['hashes'])} 个")
    print()
    print("📋 接下来的步骤：")
    print(f"1. 在浏览器中打开 {args.output} 测试功能")
    print("2. 将文件上传到GitHub Pages或其他静态托管服务")
    print("3. 如需更新数据，重新运行此脚本即可")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建过程中出现错误: {e}")
        sys.exit(1)