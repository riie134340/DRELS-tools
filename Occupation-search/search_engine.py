from fuzzywuzzy import fuzz
from difflib import get_close_matches
from config import Config


class SearchEngine:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def search(self, query):
        """主搜索函数"""
        if not query or not query.strip():
            return {
                'found': False,
                'message': '请输入要查询的职业名称'
            }

        query = query.strip()
        all_names = self.data_handler.get_all_searchable_names()

        # 1. 精确匹配
        exact_match = self.exact_search(query, all_names)
        if exact_match:
            return exact_match

        # 2. 模糊匹配
        fuzzy_match = self.fuzzy_search(query, all_names)
        if fuzzy_match:
            return fuzzy_match

        # 3. 未找到
        return {
            'found': False,
            'message': f'未找到与 "{query}" 相关的职业信息'
        }

    def exact_search(self, query, all_names):
        """精确搜索"""
        if query in all_names:
            occupation_info = self.data_handler.get_occupation_info(query)
            status_emoji = {
                'Occupied': '🔒',
                'Hold': '⏸️',
                'Available': '✅',
                '': '❓'
            }
            emoji = status_emoji.get(occupation_info['status'], '❓')

            return {
                'found': True,
                'match_type': 'exact',
                'message': f'{emoji} 找到职业：{occupation_info["occupation"]} - 状态：{occupation_info["chinese_status"]}',
                'data': occupation_info
            }
        return None

    def fuzzy_search(self, query, all_names):
        """模糊搜索"""
        best_matches = []

        # 使用fuzzywuzzy进行模糊匹配
        for name in all_names:
            ratio = fuzz.ratio(query, name)
            partial_ratio = fuzz.partial_ratio(query, name)
            token_ratio = fuzz.token_sort_ratio(query, name)

            # 取最高的相似度
            max_ratio = max(ratio, partial_ratio, token_ratio)

            if max_ratio >= Config.FUZZY_MATCH_THRESHOLD:
                best_matches.append((name, max_ratio))

        if best_matches:
            # 按相似度排序
            best_matches.sort(key=lambda x: x[1], reverse=True)
            best_match_name = best_matches[0][0]
            similarity = best_matches[0][1]

            occupation_info = self.data_handler.get_occupation_info(best_match_name)
            status_emoji = {
                'Occupied': '🔒',
                'Hold': '⏸️',
                'Available': '✅',
                '': '❓'
            }
            emoji = status_emoji.get(occupation_info['status'], '❓')

            return {
                'found': True,
                'match_type': 'fuzzy',
                'message': f'{emoji} 找到相似职业：{occupation_info["occupation"]} - 状态：{occupation_info["chinese_status"]} (相似度: {similarity}%)',
                'data': occupation_info,
                'similarity': similarity
            }

        return None

    def get_suggestions(self, query, max_suggestions=3):
        """获取搜索建议"""
        all_names = self.data_handler.get_all_searchable_names()
        suggestions = get_close_matches(query, all_names, n=max_suggestions, cutoff=0.6)
        return suggestions