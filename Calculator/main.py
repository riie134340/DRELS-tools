from map_reader import load_map_with_color
from simulator import calc_team_action_points, simulate_exploration

if __name__ == "__main__":
    # 读取地图
    grid = load_map_with_color("map/ch1.xlsx")

    # 构建一支队伍
    team = [
        {"name": "P1", "words": 0, "illustrations": {'color': 3}, "comics": [(12,'sketch')]},
        {"name": "P2", "words": 0, "illustrations": {'lineart': 8}, "comics": []},
        {"name": "P3", "words": 3500, "illustrations": {}, "comics": []},
        {"name": "P4", "words": 11200,  "illustrations": {}, "comics": []}
    ]

    # 计算行动值
    action_points = calc_team_action_points(team, pt_per_action=5)

    # 打印每个人的pt
    from score_calculator import calc_total_score

    pts = [calc_total_score(p["words"], p["illustrations"], p["comics"]) for p in team]
    print(" ".join(str(pt) for pt in pts))
    print(f"队伍总行动值: {action_points}")

    # 模拟探索
    min_e, max_e, avg_e = simulate_exploration(grid, action_points, start=(0, 0), simulations=10000)

    print(f"地图大小: {len(grid)}x{len(grid[0])}")
    print(f"总行动值: {action_points}")
    print(f"模拟次数: 10000")
    print(f"最少触发事件数: {min_e}")
    print(f"最多触发事件数: {max_e}")
    print(f"平均触发事件数: {avg_e:.2f}")
