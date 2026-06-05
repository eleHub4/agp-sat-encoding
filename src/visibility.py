from src.geometry import segment_in_polygon
from shapely.geometry import Polygon, LineString


def compute_visibility(candidates, polygon):
    n = len(candidates)
    V = [[False] * n for _ in range(n)]
    for i in range(n):
        V[i][i] = True
        for j in range(i + 1, n):
            vis = segment_in_polygon(candidates[i], candidates[j], polygon)
            V[i][j] = vis
            V[j][i] = vis
    return V


def compute_visibility_shapely(candidates, polygon):
    poly = Polygon(polygon)
    n = len(candidates)
    V = [[False] * n for _ in range(n)]
    for i in range(n):
        V[i][i] = True
        for j in range(i + 1, n):
            seg = LineString([candidates[i], candidates[j]])
            vis = poly.covers(seg)
            V[i][j] = vis
            V[j][i] = vis
    return V