import random
from score_calculator import calc_total_score

def calc_team_action_points(team, pt_per_action=5):
    """计算队伍总行动值"""
    total_pt = 0
    for player in team:
        pt = calc_total_score(player['words'], player['illustrations'], player['comics'])
        total_pt += pt
    print(f"队伍总pt: {total_pt}")
    return total_pt // pt_per_action

def simulate_exploration(grid, action_points, start=(0, 0), simulations=10000):
    """
    模拟队伍在地图上的探索：
    - grid: 事件布尔矩阵
    - action_points: 队伍可用行动值
    - start: 起点坐标
    - simulations: 模拟次数
    事件可重复触发
    """
    rows, cols = len(grid), len(grid[0])
    max_events = 0
    min_events = float('inf')
    total_events = 0

    for _ in range(simulations):
        events = 0
        ap = action_points
        pos = start

        while ap > 0:
            # 随机移动
            r, c = pos
            moves = [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
            moves = [(x, y) for x, y in moves if 0 <= x < rows and 0 <= y < cols]

            if not moves:
                break

            pos = random.choice(moves)
            ap -= 1  # 移动消耗 1 点

            # 如果是事件格且还有行动值，触发事件
            if grid[pos[0]][pos[1]] and ap > 0:
                events += 1
                ap -= 1  # 触发事件消耗 1 点

        total_events += events
        max_events = max(max_events, events)
        min_events = min(min_events, events)

    # 如果从未触发过事件，修正 min_events
    if min_events == float('inf'):
        min_events = 0

    avg_events = total_events / simulations
    return min_events/2, max_events/2, avg_events/2
