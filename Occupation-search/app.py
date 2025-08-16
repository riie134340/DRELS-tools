from flask import Flask, render_template, request, jsonify
from data_handler import DataHandler
from search_engine import SearchEngine
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据处理器和搜索引擎
data_handler = DataHandler()
search_engine = SearchEngine(data_handler)


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """搜索接口"""
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        return jsonify({
            'success': False,
            'message': '请输入要查询的才能名称'
        })

    try:
        result = search_engine.search(query)

        if result['found']:
            # 构造返回数据，不直接暴露完整职业列表
            response_data = {
                'occupation': result['data']['occupation'],
                'has_aliases': len(result['data']['aliases']) > 0,
                'match_type': result['match_type'],
                'status': result['data']['status'],
                'chinese_status': result['data']['chinese_status']
            }

            # 如果是模糊匹配，返回相似度
            if 'similarity' in result:
                response_data['similarity'] = result['similarity']

            return jsonify({
                'success': True,
                'message': result['message'],
                'data': response_data
            })
        else:
            # 提供一些搜索建议（但不暴露完整列表）
            suggestions = search_engine.get_suggestions(query)
            return jsonify({
                'success': False,
                'message': result['message'],
                'suggestions': suggestions[:2] if suggestions else []  # 最多返回2个建议
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '搜索过程中出现错误，请稍后重试'
        })


@app.route('/reload', methods=['POST'])
def reload_data():
    """重新加载数据接口（可选，用于更新数据）"""
    try:
        data_handler.reload_data()
        return jsonify({
            'success': True,
            'message': '数据重新加载成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '数据加载失败'
        })


@app.route('/stats')
def stats():
    """统计信息接口"""
    total_occupations = len(data_handler.occupations_data)
    return jsonify({
        'total_occupations': total_occupations,
        'data_source': Config.DATA_SOURCE
    })


if __name__ == '__main__':
    print(f"职业搜索系统启动中...")
    print(f"数据源: {'在线表格' if Config.DATA_SOURCE == 'online' else '本地Excel文件'}")
    print(f"访问地址: http://localhost:5000")
    app.run(debug=Config.DEBUG)