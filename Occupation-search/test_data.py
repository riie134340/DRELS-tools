import pandas as pd
import os

# 检查文件是否存在
file_path = "data/occupations.xlsx"
if os.path.exists(file_path):
    print(f"✅ 文件存在: {file_path}")

    try:
        # 尝试读取Excel
        df = pd.read_excel(file_path)
        print(f"✅ 成功读取Excel，共 {len(df)} 行")
        print("\n列名:", df.columns.tolist())
        print("\n前5行数据:")
        print(df.head())

    except Exception as e:
        print(f"❌ 读取Excel失败: {e}")

else:
    print(f"❌ 文件不存在: {file_path}")
    print("当前目录:", os.getcwd())
    print("data目录内容:", os.listdir("data") if os.path.exists("data") else "data目录不存在")