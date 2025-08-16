import pandas as pd
import requests
from io import BytesIO, StringIO
from config import Config
import re
from bs4 import BeautifulSoup
import chardet


class DataHandler:
    def __init__(self):
        self.occupations_data = []
        self.load_data()

    def load_data(self):
        """根据配置加载数据"""
        try:
            if Config.DATA_SOURCE == 'online':
                self.load_from_google_sheets()
            else:
                self.load_from_local()
            print(f"成功加载 {len(self.occupations_data)} 条职业数据")
        except Exception as e:
            print(f"数据加载失败: {e}")
            self.occupations_data = []

    def load_from_local(self):
        """从本地Excel文件加载数据"""
        # 尝试不同的编码方式读取Excel
        try:
            df = pd.read_excel(Config.LOCAL_EXCEL_PATH, engine='openpyxl')
            print("使用openpyxl引擎成功读取Excel文件")
        except:
            try:
                df = pd.read_excel(Config.LOCAL_EXCEL_PATH, engine='xlrd')
                print("使用xlrd引擎成功读取Excel文件")
            except:
                # 如果Excel读取失败，尝试先转换为CSV
                print("Excel读取失败，请确保文件格式正确")
                return

        self.process_dataframe(df)

    def load_from_google_sheets(self):
        """从Google Sheets加载数据，修复编码问题"""
        if not Config.TENCENT_SHEET_URL:
            raise ValueError("Google Sheets URL未配置")

        sheet_url = Config.TENCENT_SHEET_URL

        # 提取文档ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            raise ValueError("无效的Google Sheets链接格式")

        sheet_id = match.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        print(f"Google Sheets CSV导出链接: {csv_url}")

        try:
            # 设置请求头，确保正确的编码处理
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(csv_url, headers=headers)
            response.raise_for_status()

            # 检查是否需要权限
            if "accounts.google.com" in response.url or "请求访问权限" in response.text:
                raise ValueError("Google Sheets需要公开访问权限，请设置为'获得链接的任何人都可以查看'")

            # 检测编码
            raw_content = response.content
            detected_encoding = chardet.detect(raw_content)
            print(f"检测到的编码: {detected_encoding}")

            # 尝试使用检测到的编码
            try:
                if detected_encoding['encoding']:
                    content = raw_content.decode(detected_encoding['encoding'])
                else:
                    content = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                # 如果解码失败，尝试常见编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
                content = None
                for encoding in encodings:
                    try:
                        content = raw_content.decode(encoding)
                        print(f"成功使用 {encoding} 编码解码")
                        break
                    except UnicodeDecodeError:
                        continue

                if content is None:
                    raise ValueError("无法解码CSV内容，请检查文件编码")

            # 使用pandas读取CSV
            from io import StringIO
            df = pd.read_csv(StringIO(content))

            print(f"成功从Google Sheets读取 {len(df)} 行数据")
            print(f"原始列名: {df.columns.tolist()}")

            # 清理列名中的特殊字符
            df.columns = df.columns.str.strip()
            print(f"清理后列名: {df.columns.tolist()}")

            # 显示前几行数据用于调试
            print("前3行数据:")
            for i, row in df.head(3).iterrows():
                print(f"第{i + 1}行: {dict(row)}")

            self.process_dataframe(df)
            return

        except Exception as e:
            print(f"CSV方法失败: {e}")

            # 尝试TSV格式作为备选
            tsv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=tsv"
            print(f"尝试TSV格式: {tsv_url}")

            try:
                response = requests.get(tsv_url, headers=headers)
                response.raise_for_status()

                # 处理编码
                raw_content = response.content
                detected_encoding = chardet.detect(raw_content)

                if detected_encoding['encoding']:
                    content = raw_content.decode(detected_encoding['encoding'])
                else:
                    content = raw_content.decode('utf-8')

                # 读取TSV (制表符分隔)
                df = pd.read_csv(StringIO(content), sep='\t')
                print(f"TSV格式成功读取 {len(df)} 行数据")
                print(f"TSV列名: {df.columns.tolist()}")

                self.process_dataframe(df)
                return

            except Exception as tsv_error:
                print(f"TSV方法也失败: {tsv_error}")

        raise ValueError("无法从Google Sheets获取数据，请检查链接权限设置")

    def process_dataframe(self, df):
        """处理DataFrame，提取职业信息"""
        self.occupations_data = []

        print(f"处理DataFrame - 列名: {df.columns.tolist()}")
        print(f"DataFrame形状: {df.shape}")

        # 处理可能的列名变体
        occupation_col = None
        alias_col = None
        status_col = None

        # 查找匹配的列名
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(keyword in col_lower for keyword in ['才能', '职业', 'occupation', 'job']):
                occupation_col = col
            elif any(keyword in col_lower for keyword in ['别称', 'alias', '别名']):
                alias_col = col
            elif any(keyword in col_lower for keyword in ['状态', 'status', '审核']):
                status_col = col

        print(f"识别的列: 职业={occupation_col}, 别称={alias_col}, 状态={status_col}")

        if not occupation_col:
            # 如果找不到明确的职业列，使用第一列
            occupation_col = df.columns[0]
            print(f"未找到职业列，使用第一列: {occupation_col}")

        for index, row in df.iterrows():
            try:
                # 获取职业名称
                occupation = ""
                if occupation_col and pd.notna(row.get(occupation_col)):
                    occupation = str(row[occupation_col]).strip()

                # 获取别称
                aliases = ""
                if alias_col and pd.notna(row.get(alias_col)):
                    aliases = str(row[alias_col]).strip()

                # 获取状态
                status = ""
                if status_col and pd.notna(row.get(status_col)):
                    status = str(row[status_col]).strip()

                # 只处理有效的职业名称
                if occupation and occupation != 'nan':
                    # 处理别称
                    alias_list = []
                    if aliases and aliases != 'nan':
                        # 支持多种分隔符
                        import re
                        alias_list = [alias.strip() for alias in re.split('[,，、;；/]', aliases) if alias.strip()]

                    # 状态映射
                    status_map = {
                        'Occupied': '已被占用',
                        'Hold': '暂时保留',
                        'Available': '可用',
                        '已占用': '已被占用',
                        '保留': '暂时保留',
                        '可用': '可用'
                    }

                    chinese_status = status_map.get(status, '未知状态')

                    occupation_data = {
                        'occupation': occupation,
                        'aliases': alias_list,
                        'status': status,
                        'chinese_status': chinese_status,
                        'all_names': [occupation] + alias_list
                    }

                    self.occupations_data.append(occupation_data)

                    print(f"处理职业 #{index + 1}: {occupation} (状态: {status})")
                    if alias_list:
                        print(f"  别称: {alias_list}")

            except Exception as e:
                print(f"处理第{index + 1}行时出错: {e}")
                continue

        print(f"最终成功处理了 {len(self.occupations_data)} 个职业")

    def get_all_searchable_names(self):
        """获取所有可搜索的名称列表"""
        all_names = []
        for item in self.occupations_data:
            all_names.extend(item['all_names'])
        return all_names

    def get_occupation_info(self, name):
        """根据名称获取职业信息"""
        for item in self.occupations_data:
            if name in item['all_names']:
                return item
        return None

    def reload_data(self):
        """重新加载数据"""
        self.load_data()

    def print_debug_info(self):
        """打印调试信息"""
        print("\n=== 数据库调试信息 ===")
        print(f"总职业数: {len(self.occupations_data)}")

        if self.occupations_data:
            print("\n前5个职业示例:")
            for i, item in enumerate(self.occupations_data[:5]):
                print(f"{i + 1}. 职业: {item['occupation']}")
                print(f"   别称: {item['aliases']}")
                print(f"   状态: {item['status']} ({item['chinese_status']})")
                print(f"   所有可搜索名称: {item['all_names']}")
                print()

        # 按状态统计
        status_count = {}
        for item in self.occupations_data:
            status = item['status']
            status_count[status] = status_count.get(status, 0) + 1

        print("状态分布:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        print("=" * 30)