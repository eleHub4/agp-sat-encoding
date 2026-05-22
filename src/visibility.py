from src.geometry import cross, sub, add, scale, points_equal, segment_in_polygon, point_in_polygon

def compute_visibility(candidates, polygon):
    n = len(candidates)
    V = [[False] * n for _ in range(n)]
    for i in range(n):
        V[i][i] = True
        for j in range(i+1, n):
            vis = segment_in_polygon(candidates[i], candidates[j], polygon)
            V[i][j] = vis
            V[j][i] = vis
    return V
