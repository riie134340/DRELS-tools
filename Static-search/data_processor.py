#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职业才能数据预处理工具
用于将Excel文件或Google Sheets转换为静态网页可用的加密数据
"""

import pandas as pd
import json
import re
import argparse
from typing import Dict, List, Tuple, Set
import hashlib
from difflib import SequenceMatcher
from rapidfuzz import fuzz
import jieba


class DataProcessor:
    def __init__(self):
        self.data = None
        self.processed_data = {
            'hashes': {},
            'fuzzy_map': {},
            'reverse_map': {},  # 用于调试，实际不会输出到前端
            'total_count': 0
        }

    def simple_hash(self, text: str) -> str:
        """简单哈希函数，与JavaScript版本保持一致"""
        text = str(text).lower().strip()
        hash_value = 0
        for char in text:
            hash_value = ((hash_value << 5) - hash_value) + ord(char)
            hash_value = hash_value & 0xFFFFFFFF  # 保持32位
            # 确保结果为正数
            if hash_value > 0x7FFFFFFF:
                hash_value = hash_value - 0x100000000
        return str(abs(hash_value))

    def load_from_excel(self, file_path: str, name_column: str = None, status_column: str = None,
                        aliases_column: str = None, fuzzy_column: str = None):
        """从Excel文件加载数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            print(f"成功读取Excel文件：{file_path}")
            print(f"数据行数：{len(df)}")
            print(f"列名：{list(df.columns)}")

            # 自动检测列名或使用用户指定的列名
            if not name_column:
                name_column = self._detect_name_column(df.columns)
            if not status_column:
                status_column = self._detect_status_column(df.columns)
            if not aliases_column:
                aliases_column = self._detect_aliases_column(df.columns)

            print(f"使用列映射：")
            print(f"  职业名称列：{name_column}")
            print(f"  状态列：{status_column}")
            print(f"  别称列：{aliases_column}")

            # 处理数据
            self._process_dataframe(df, name_column, status_column, aliases_column, fuzzy_column)

        except Exception as e:
            print(f"读取Excel文件失败：{e}")
            return False
        return True

    def load_from_google_sheets(self, sheet_url: str, name_column: str = None, status_column: str = None,
                                aliases_column: str = None,  fuzzy_column: str = None):
        """从Google Sheets加载数据"""
        try:
            # 转换Google Sheets URL为CSV导出URL
            if '/edit' in sheet_url:
                csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=').replace('/edit',
                                                                                             '/export?format=csv')
            else:
                csv_url = sheet_url

            # 读取在线表格
            df = pd.read_csv(csv_url)
            print(f"成功读取Google Sheets：{sheet_url}")
            print(f"数据行数：{len(df)}")
            print(f"列名：{list(df.columns)}")

            # 自动检测列名或使用用户指定的列名
            if not name_column:
                name_column = self._detect_name_column(df.columns)
            if not status_column:
                status_column = self._detect_status_column(df.columns)
            if not aliases_column:
                aliases_column = self._detect_aliases_column(df.columns)

            print(f"使用列映射：")
            print(f"  职业名称列：{name_column}")
            print(f"  状态列：{status_column}")
            print(f"  别称列：{aliases_column}")

            # 处理数据
            self._process_dataframe(df, name_column, status_column, aliases_column, fuzzy_column)

        except Exception as e:
            print(f"读取Google Sheets失败：{e}")
            return False
        return True

    def _detect_name_column(self, columns) -> str:
        """自动检测职业名称列"""
        name_keywords = ['名称', 'name', '职业', 'job', 'occupation', 'title', '才能', 'talent']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                return col
        # 如果没找到，返回第一列
        return columns[0] if len(columns) > 0 else None

    def _detect_status_column(self, columns) -> str:
        """自动检测状态列"""
        status_keywords = ['状态', 'status', '情况', 'state', '可用', 'available']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in status_keywords):
                return col
        # 如果没找到，尝试找包含Available/Occupied等词的列
        for col in columns:
            return col if col != self._detect_name_column(columns) else None
        return None

    def _detect_aliases_column(self, columns) -> str:
        """自动检测别称列"""
        alias_keywords = ['别称', 'alias', 'aliases', '别名', 'alternative', '其他', 'other']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in alias_keywords):
                return col
        return None

    def _process_dataframe(self, df: pd.DataFrame, name_column: str, status_column: str, aliases_column: str, fuzzy_column: str):
        """处理DataFrame数据"""
        processed_count = 0

        for index, row in df.iterrows():
            name = str(row[name_column]).strip() if pd.notna(row[name_column]) else ""
            if not name or name.lower() in ['nan', 'none', '']:
                continue

            # 获取状态
            status = str(row[status_column]).strip() if status_column and pd.notna(row[status_column]) else "Available"
            # 标准化状态值
            status = self._normalize_status(status)

            # 获取别称
            aliases = []
            if aliases_column and pd.notna(row[aliases_column]):
                aliases_str = str(row[aliases_column]).strip()
                if aliases_str and aliases_str.lower() not in ['nan', 'none', '']:
                    # 支持多种分隔符
                    aliases = [alias.strip() for alias in re.split(r'[,，;；|/]', aliases_str) if alias.strip()]

            # 获取模糊词
            fuzzy_keywords = []
            if fuzzy_column and pd.notna(row[fuzzy_column]):
                fuzzy_str = str(row[fuzzy_column]).strip()
                if fuzzy_str and fuzzy_str.lower() not in ['nan', 'none', '']:
                    fuzzy_keywords = [kw.strip() for kw in re.split(r'[,，;；|/ ]', fuzzy_str) if kw.strip()]

            # 生成主要名称的哈希
            main_hash = self.simple_hash(name)
            # 存 fuzzy 映射
            for fuzzy_kw in fuzzy_keywords:
                fuzzy_hash = self.simple_hash(fuzzy_kw)
                if fuzzy_hash not in self.processed_data['fuzzy_map']:
                    self.processed_data['fuzzy_map'][fuzzy_hash] = []
                if main_hash not in self.processed_data['fuzzy_map'][fuzzy_hash]:
                    self.processed_data['fuzzy_map'][fuzzy_hash].append(main_hash)

            # 存储数据
            self.processed_data['hashes'][main_hash] = {
                'status': status,
                'aliases': aliases,
                'main_name': name
            }

            # 存储反向映射（用于调试）
            self.processed_data['reverse_map'][main_hash] = name

            # 为别称生成哈希
            for alias in aliases:
                alias_hash = self.simple_hash(alias)
                self.processed_data['hashes'][alias_hash] = {
                    'status': status,
                    'aliases': [],
                    'is_alias': True,
                    'main_name': name
                }
                self.processed_data['reverse_map'][alias_hash] = f"{alias} (别称: {name})"

            processed_count += 1

        self.processed_data['total_count'] = processed_count
        print(f"成功处理 {processed_count} 条记录")

        # 生成模糊匹配映射
        self._generate_fuzzy_mapping()

    def _normalize_status(self, status: str) -> str:
        """标准化状态值"""
        status = status.lower()
        if status in ['available', '可用', '空闲', '未占用']:
            return 'Available'
        elif status in ['occupied', '已占用', '占用', '使用中']:
            return 'Occupied'
        elif status in ['hold', 'holding', '保留', '预留', '暂停']:
            return 'Hold'
        else:
            return 'Available'  # 默认为可用

    def _generate_fuzzy_mapping(self):
        """生成模糊匹配映射，支持关键词搜索"""
        print("生成模糊匹配映射...")
        names = list(self.processed_data['reverse_map'].values())

        for name1 in names:
            # 原始名称（去掉别称标记）
            base_name = name1.split('(')[0].strip()
            name1_hash = self.simple_hash(base_name)

            # 用 jieba 分词，比如 "手术医生" -> ["手术","医生"]
            keywords = list(jieba.cut(base_name))
            keywords.append(base_name)  # 全称也要算进去

            for kw in keywords:
                kw = kw.strip()
                if not kw or len(kw) == 1:  # 可选：跳过单字
                    continue

                kw_hash = self.simple_hash(kw)

                if kw_hash not in self.processed_data['fuzzy_map']:
                    self.processed_data['fuzzy_map'][kw_hash] = []

                if name1_hash not in self.processed_data['fuzzy_map'][kw_hash]:
                    self.processed_data['fuzzy_map'][kw_hash].append(name1_hash)

    def generate_static_html(self, template_path: str, output_path: str):
        """生成包含数据的静态HTML文件"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 准备要注入的数据（不包含reverse_map）
            data_to_inject = {
                'hashes': self.processed_data['hashes'],
                'fuzzy_map': self.processed_data['fuzzy_map'],
                'total_count': self.processed_data['total_count']
            }

            # 将数据转换为JSON字符串
            data_json = json.dumps(data_to_inject, ensure_ascii=False, separators=(',', ':'))

            # 替换模板中的数据占位符
            html_content = html_content.replace(
                'const ENCRYPTED_DATA = {\n            // 示例数据结构，实际数据会在构建时注入\n            hashes: {\n                // "hash1": { status: "Available", aliases: ["alias1", "alias2"] },\n                // "hash2": { status: "Occupied", aliases: [] }\n            },\n            fuzzy_map: {\n                // "fuzzy_hash1": ["hash1", "hash2"]\n            },\n            total_count: 0\n        };',
                f'const ENCRYPTED_DATA = {data_json};'
            )

            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"成功生成静态HTML文件：{output_path}")
            print(f"数据统计：")
            print(f"  总记录数：{self.processed_data['total_count']}")
            print(f"  哈希条目数：{len(self.processed_data['hashes'])}")
            print(f"  模糊匹配映射数：{len(self.processed_data['fuzzy_map'])}")

        except Exception as e:
            print(f"生成静态HTML失败：{e}")
            return False
        return True

    def save_debug_info(self, output_path: str):
        """保存调试信息（包含原始名称映射）"""
        debug_data = {
            'reverse_map': self.processed_data['reverse_map'],
            'total_count': self.processed_data['total_count'],
            'sample_hashes': {k: v for k, v in list(self.processed_data['hashes'].items())[:5]}
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print(f"调试信息已保存至：{output_path}")
        except Exception as e:
            print(f"保存调试信息失败：{e}")


def main():
    parser = argparse.ArgumentParser(description='职业才能数据预处理工具')
    parser.add_argument('--excel', type=str, help='Excel文件路径')
    parser.add_argument('--sheets', type=str, help='Google Sheets URL')
    parser.add_argument('--template', type=str, default='template.html', help='HTML模板文件路径')
    parser.add_argument('--output', type=str, default='index.html', help='输出HTML文件路径')
    parser.add_argument('--debug', type=str, help='调试信息输出文件路径')
    parser.add_argument('--name-col', type=str, help='职业名称列名')
    parser.add_argument('--status-col', type=str, help='状态列名')
    parser.add_argument('--aliases-col', type=str, help='别称列名')
    parser.add_argument('--fuzzy-col', type=str, help='模糊词列名')

    args = parser.parse_args()

    if not args.excel and not args.sheets:
        print("错误：必须指定 --excel 或 --sheets 参数")
        return

    processor = DataProcessor()

    # 加载数据
    if args.excel:
        if not processor.load_from_excel(args.excel, args.name_col, args.status_col, args.aliases_col, args.fuzzy_col):
            return
    elif args.sheets:
        if not processor.load_from_google_sheets(args.sheets, args.name_col, args.status_col, args.aliases_col, args.fuzzy_col):
            return

    # 生成静态HTML
    if not processor.generate_static_html(args.template, args.output):
        return

    # 保存调试信息
    if args.debug:
        processor.save_debug_info(args.debug)

    print("\n处理完成！")
    print(f"静态网页已生成：{args.output}")
    print("现在可以将生成的HTML文件部署到GitHub Pages或其他静态网站托管服务。")


if __name__ == '__main__':
    main()