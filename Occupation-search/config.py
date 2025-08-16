# 配置文件
class Config:
    # Google Sheets相关配置
    TENCENT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1zgmpW6Txc2_DYZ-XxHjxbYVqKR0mm928/edit?usp=sharing&ouid=114134414249936425386&rtpof=true&sd=true"

    # 本地文件路径
    LOCAL_EXCEL_PATH = "data/occupations.xlsx"

    # 搜索匹配阈值
    FUZZY_MATCH_THRESHOLD = 70  # 模糊匹配相似度阈值（0-100）

    # 数据源配置 ('local' 或 'online')
    DATA_SOURCE = 'online'

    # Flask配置
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = True