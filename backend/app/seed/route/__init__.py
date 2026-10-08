"""Core-route questions from the 12 topic lists, rated ≤ 1700 (or unrated), in route order.

Same format as `seed/questions.py`. LeetCode.cn-only problems (LCP, LCS, 面试题)
have n=None, a display `ref` such as "LCP 67", and a leetcode.cn `url`.
"""

from .grid_dfs import QUESTIONS as GRID_DFS
from .tree_dfs import QUESTIONS as TREE_DFS

ROUTE_QUESTIONS = [*TREE_DFS, *GRID_DFS]
