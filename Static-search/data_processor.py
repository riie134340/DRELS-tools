#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职业才能数据预处理工具 - 修复模糊匹配版本
用于将Excel文件或Google Sheets转换为静态网页可用的加密数据
"""

import pandas as pd
import json
import re
import argparse
import jieba
import unicodedata
from rapidfuzz import fuzz


class DataProcessor:
    def __init__(self, debug=False):
        self.debug = debug
        self.processed_data = {
            'hashes': {},
            'fuzzy_map': {},
            'reverse_map': {},  # 用于调试，实际不会输出到前端
            'total_count': 0
        }

    def log(self, *args, **kwargs):
        """仅在 debug 模式下输出日志"""
        if self.debug:
            print(*args, **kwargs)

    def simple_hash(self, text: str) -> str:
        """简单哈希函数，与JavaScript版本保持一致"""
        # 统一大小写、去空格、Unicode 归一化（NFKC）
        text = unicodedata.normalize("NFKC", str(text)).lower().strip()
        hash_value = 0
        for char in text:
            char_code = ord(char)
            hash_value = ((hash_value << 5) - hash_value) + char_code
            hash_value = ((hash_value + 0x80000000) % 0x100000000) - 0x80000000
        return str(abs(hash_value))

    def load_from_excel(self, file_path: str, name_column: str = None, status_column: str = None,
                        aliases_column: str = None, fuzzy_column: str = None):
        """从Excel文件加载数据"""
        try:
            df = pd.read_excel(file_path)
            print(f"成功读取Excel文件：{file_path}")
            print(f"数据行数：{len(df)}")
            print(f"列名：{list(df.columns)}")

            if not name_column:
                name_column = self._detect_name_column(df.columns)
            if not status_column:
                status_column = self._detect_status_column(df.columns)
            if not aliases_column:
                aliases_column = self._detect_aliases_column(df.columns)
            if not fuzzy_column:
                fuzzy_column = self._detect_fuzzy_column(df.columns)

            print(f"使用列映射：")
            print(f"  职业名称列：{name_column}")
            print(f"  状态列：{status_column}")
            print(f"  别称列：{aliases_column}")
            print(f"  模糊词列：{fuzzy_column}")

            self._process_dataframe(df, name_column, status_column, aliases_column, fuzzy_column)

        except Exception as e:
            print(f"读取Excel文件失败：{e}")
            return False
        return True

    def load_from_google_sheets(self, sheet_url: str, name_column: str = None, status_column: str = None,
                                aliases_column: str = None, fuzzy_column: str = None):
        """从Google Sheets加载数据"""
        try:
            if '/edit' in sheet_url:
                csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=').replace('/edit',
                                                                                             '/export?format=csv')
            else:
                csv_url = sheet_url

            df = pd.read_csv(csv_url)
            print(f"成功读取Google Sheets：{sheet_url}")
            print(f"数据行数：{len(df)}")
            print(f"列名：{list(df.columns)}")

            if not name_column:
                name_column = self._detect_name_column(df.columns)
            if not status_column:
                status_column = self._detect_status_column(df.columns)
            if not aliases_column:
                aliases_column = self._detect_aliases_column(df.columns)
            if not fuzzy_column:
                fuzzy_column = self._detect_fuzzy_column(df.columns)

            print(f"使用列映射：")
            print(f"  职业名称列：{name_column}")
            print(f"  状态列：{status_column}")
            print(f"  别称列：{aliases_column}")
            print(f"  模糊词列：{fuzzy_column}")

            self._process_dataframe(df, name_column, status_column, aliases_column, fuzzy_column)

        except Exception as e:
            print(f"读取Google Sheets失败：{e}")
            return False
        return True

    def _detect_name_column(self, columns) -> str:
        name_keywords = ['名称', 'name', '职业', 'job', 'occupation', 'title', '才能', 'talent']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                return col
        return columns[0] if len(columns) > 0 else None

    def _detect_status_column(self, columns) -> str:
        status_keywords = ['状态', 'status', '情况', 'state', '可用', 'available']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in status_keywords):
                return col
        for col in columns:
            return col if col != self._detect_name_column(columns) else None
        return None

    def _detect_aliases_column(self, columns) -> str:
        alias_keywords = ['别称', 'alias', 'aliases', '别名', 'alternative', '其他', 'other']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in alias_keywords):
                return col
        return None

    def _detect_fuzzy_column(self, columns) -> str:
        fuzzy_keywords = ['模糊词', '模糊', 'fuzzy', '关键词', 'keyword', 'keywords', '标签', 'tag', 'tags']
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in fuzzy_keywords):
                return col
        return None

    def _process_dataframe(self, df: pd.DataFrame, name_column: str, status_column: str, aliases_column: str,
                           fuzzy_column: str):
        processed_count = 0

        for index, row in df.iterrows():
            name = str(row[name_column]).strip() if pd.notna(row[name_column]) else ""
            if not name or name.lower() in ['nan', 'none', '']:
                continue

            status = str(row[status_column]).strip() if status_column and pd.notna(row[status_column]) else "Available"
            status = self._normalize_status(status)

            aliases = []
            if aliases_column and pd.notna(row[aliases_column]):
                aliases_str = str(row[aliases_column]).strip()
                if aliases_str and aliases_str.lower() not in ['nan', 'none', '']:
                    aliases = [alias.strip() for alias in re.split(r'[,，;；|/]', aliases_str) if alias.strip()]

            fuzzy_keywords = []
            if fuzzy_column and pd.notna(row[fuzzy_column]):
                fuzzy_str = str(row[fuzzy_column]).strip()
                if fuzzy_str and fuzzy_str.lower() not in ['nan', 'none', '']:
                    fuzzy_keywords = [kw.strip() for kw in re.split(r'[,，;；|/\s]', fuzzy_str) if kw.strip()]

            main_hash = self.simple_hash(name)

            self.processed_data['hashes'][main_hash] = {
                'status': status,
                'aliases': aliases,
                'main_name': name
            }
            self.processed_data['reverse_map'][main_hash] = name

            for alias in aliases:
                if alias == name:
                    continue
                alias_hash = self.simple_hash(alias)
                self.processed_data['hashes'][alias_hash] = {
                    'status': status,
                    'aliases': [],
                    'is_alias': True,
                    'main_name': name
                }
                self.processed_data['reverse_map'][alias_hash] = f"{alias} (别称: {name})"

            # 调试输出
            self.log(f"处理 '{name}' 的模糊词: {fuzzy_keywords}")
            for fuzzy_kw in fuzzy_keywords:
                fuzzy_hash = self.simple_hash(fuzzy_kw)
                if fuzzy_hash not in self.processed_data['fuzzy_map']:
                    self.processed_data['fuzzy_map'][fuzzy_hash] = []
                if main_hash not in self.processed_data['fuzzy_map'][fuzzy_hash]:
                    self.processed_data['fuzzy_map'][fuzzy_hash].append(main_hash)
                    self.log(f"  添加映射: '{fuzzy_kw}' (hash:{fuzzy_hash}) -> '{name}' (hash:{main_hash})")

            processed_count += 1

        self.processed_data['total_count'] = processed_count
        print(f"✅ 成功处理 {processed_count} 条记录")

        self._generate_smart_fuzzy_mapping()

    def _normalize_status(self, status: str) -> str:
        status = status.lower()
        if status in ['available', '可用', '空闲', '未占用']:
            return 'Available'
        elif status in ['occupied', '已占用', '占用', '使用中']:
            return 'Occupied'
        elif status in ['hold', 'holding', '保留', '预留', '暂停']:
            return 'Hold'
        else:
            return 'Available'

    def _generate_smart_fuzzy_mapping(self):
        self.log("生成智能模糊匹配映射...")

        main_names = []
        for hash_key, data in self.processed_data['hashes'].items():
            if not data.get('is_alias', False):
                main_names.append((hash_key, data['main_name']))

        self.log(f"处理 {len(main_names)} 个主要名称")

        for main_hash, main_name in main_names:
            self.log(f"为 '{main_name}' 生成模糊映射")

            name_hash = self.simple_hash(main_name)
            self._add_to_fuzzy_map(name_hash, main_hash, f"完整名称: {main_name}")

            try:
                keywords = list(jieba.cut(main_name))
                self.log(f"  jieba分词结果: {keywords}")

                for keyword in keywords:
                    keyword = keyword.strip()
                    if len(keyword) <= 1 or not keyword or keyword.isspace():
                        continue
                    if all(not c.isalnum() for c in keyword):
                        continue
                    keyword_hash = self.simple_hash(keyword)
                    self._add_to_fuzzy_map(keyword_hash, main_hash, f"关键词: {keyword} -> {main_name}")

            except Exception as e:
                self.log(f"  jieba分词失败: {e}")

            if len(main_name) >= 2:
                for i in range(2, min(len(main_name) + 1, 5)):
                    prefix = main_name[:i]
                    prefix_hash = self.simple_hash(prefix)
                    self._add_to_fuzzy_map(prefix_hash, main_hash, f"前缀: {prefix} -> {main_name}")

        self.log(f"生成了 {len(self.processed_data['fuzzy_map'])} 个模糊匹配映射")

    def _add_to_fuzzy_map(self, fuzzy_hash, main_hash, debug_info):
        if fuzzy_hash not in self.processed_data['fuzzy_map']:
            self.processed_data['fuzzy_map'][fuzzy_hash] = []
        if main_hash not in self.processed_data['fuzzy_map'][fuzzy_hash]:
            self.processed_data['fuzzy_map'][fuzzy_hash].append(main_hash)
            self.log(f"    {debug_info}")

    def generate_static_html(self, template_path: str, output_path: str):
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            data_to_inject = {
                'hashes': self.processed_data['hashes'],
                'fuzzy_map': self.processed_data['fuzzy_map'],
                'total_count': self.processed_data['total_count']
            }

            data_json = json.dumps(data_to_inject, ensure_ascii=False, separators=(',', ':'))

            html_content = html_content.replace(
                'const ENCRYPTED_DATA = {\n            // 示例数据结构，实际数据会在构建时注入\n            hashes: {\n                // "hash1": { status: "Available", aliases: ["alias1", "alias2"] },\n                // "hash2": { status: "Occupied", aliases: [] }\n            },\n            fuzzy_map: {\n                // "fuzzy_hash1": ["hash1", "hash2"]\n            },\n            total_count: 0\n        };',
                f'const ENCRYPTED_DATA = {data_json};'
            )

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"✅ 成功生成静态HTML文件：{output_path}")
            print(f"📊 数据统计：总记录数 {self.processed_data['total_count']} | 哈希 {len(self.processed_data['hashes'])} | 模糊映射 {len(self.processed_data['fuzzy_map'])}")

        except Exception as e:
            print(f"生成静态HTML失败：{e}")
            return False
        return True

    def save_debug_info(self, output_path: str):
        debug_data = {
            'reverse_map': self.processed_data['reverse_map'],
            'fuzzy_map_sample': dict(list(self.processed_data['fuzzy_map'].items())[:20]),
            'total_count': self.processed_data['total_count'],
            'sample_hashes': {k: v for k, v in list(self.processed_data['hashes'].items())[:10]},
            'fuzzy_map_stats': {
                'total_fuzzy_entries': len(self.processed_data['fuzzy_map']),
                'sample_mappings': []
            }
        }

        for fuzzy_hash, main_hashes in list(self.processed_data['fuzzy_map'].items())[:10]:
            debug_data['fuzzy_map_stats']['sample_mappings'].append({
                'fuzzy_hash': fuzzy_hash,
                'mapped_to': [self.processed_data['reverse_map'].get(h, 'unknown') for h in main_hashes]
            })

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print(f"🔍 调试信息已保存至：{output_path}")
        except Exception as e:
            print(f"保存调试信息失败：{e}")


def main():
    parser = argparse.ArgumentParser(description='职业才能数据预处理工具')
    parser.add_argument('--excel', type=str, help='Excel文件路径')
    parser.add_argument('--sheets', type=str, help='Google Sheets URL')
    parser.add_argument('--template', type=str, default='template.html', help='HTML模板文件路径')
    parser.add_argument('--output', type=str, default='index.html', help='输出HTML文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试输出')
    parser.add_argument('--debug-file', type=str, help='指定调试信息输出文件路径')
    parser.add_argument('--name-col', type=str, help='职业名称列名')
    parser.add_argument('--status-col', type=str, help='状态列名')
    parser.add_argument('--aliases-col', type=str, help='别称列名')
    parser.add_argument('--fuzzy-col', type=str, help='模糊词列名')

    args = parser.parse_args()

    if not args.excel and not args.sheets:
        print("错误：必须指定 --excel 或 --sheets 参数")
        return

    processor = DataProcessor(debug=args.debug)

    if args.excel:
        if not processor.load_from_excel(args.excel, args.name_col, args.status_col, args.aliases_col, args.fuzzy_col):
            return
    elif args.sheets:
        if not processor.load_from_google_sheets(args.sheets, args.name_col, args.status_col, args.aliases_col,
                                                 args.fuzzy_col):
            return

    if not processor.generate_static_html(args.template, args.output):
        return

    if args.debug:
        debug_file = args.debug_file or args.output.replace('.html', '_debug.json')
        processor.save_debug_info(debug_file)

    print("\n🎉 处理完成！")
    print(f"📄 静态网页已生成：{args.output}")
    if args.debug:
        print(f"🔍 调试数据已保存：{debug_file}")


if __name__ == '__main__':
    main()
