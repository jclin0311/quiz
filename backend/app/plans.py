"""Study plans, after "如何科学刷题" (leetcode.cn/discuss/post/3141566).

Each plan keeps its own Practice, Review and Extra history. Mastery and the
progress analysis span every plan; only the question pool and the way
questions are chosen differ.

- topic:  Topic training. Follow the roadmap one pattern at a time, easier
          problems first, and unlock a topic only once its prerequisites are ready.
- random: Random training. Topic-blind mixed sets for people past the basics:
          no roadmap, one question per topic, and topic tags stay hidden until
          answered so the pattern has to be recognized.
- sprint: Sprint training. Interview prep under time pressure: LeetCode Hot 100
          first, then Top Interview 150.
"""

from dataclasses import dataclass

DEFAULT_PLAN = "topic"


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    roadmap: bool  # gate topics behind their prerequisites
    per_topic_cap: int  # questions per topic in a set before topping up
    hide_topics: bool  # hide topic tags until answered


PLANS = {
    "topic": Plan("topic", "Topic", roadmap=True, per_topic_cap=3, hide_topics=False),
    "random": Plan("random", "Random", roadmap=False, per_topic_cap=1, hide_topics=True),
    "sprint": Plan("sprint", "Sprint", roadmap=False, per_topic_cap=2, hide_topics=False),
}

# LeetCode problem numbers.
HOT_100 = frozenset({
    1, 49, 128, 283, 11, 15, 42, 3, 438, 560, 239, 76, 53, 56, 189, 238, 41, 73, 54, 48,
    240, 160, 206, 234, 141, 142, 21, 2, 19, 24, 25, 138, 148, 23, 146, 94, 104, 226, 101,
    543, 102, 108, 98, 230, 199, 114, 105, 437, 236, 124, 200, 994, 207, 208, 46, 78, 17,
    39, 22, 79, 131, 51, 35, 74, 34, 33, 153, 4, 20, 155, 394, 739, 84, 215, 347, 295, 121,
    55, 45, 763, 70, 118, 198, 279, 322, 139, 300, 152, 416, 32, 62, 64, 5, 1143, 72, 136,
    169, 75, 31, 287,
})
TOP_INTERVIEW_150 = frozenset({
    88, 27, 26, 80, 169, 189, 121, 122, 55, 45, 274, 380, 238, 134, 135, 42, 13, 12, 58, 14,
    151, 6, 28, 68, 125, 392, 167, 11, 15, 209, 3, 30, 76, 36, 54, 48, 73, 289, 383, 205,
    290, 242, 49, 1, 202, 219, 128, 228, 56, 57, 452, 20, 71, 155, 150, 224, 141, 2, 21, 138,
    92, 25, 19, 82, 61, 86, 146, 104, 100, 226, 101, 105, 106, 117, 114, 112, 129, 124, 173,
    222, 236, 199, 637, 102, 103, 530, 230, 98, 200, 130, 133, 399, 207, 210, 909, 433, 127,
    208, 211, 212, 17, 77, 46, 39, 52, 22, 79, 108, 148, 427, 23, 53, 918, 35, 74, 162, 33,
    34, 153, 4, 215, 502, 373, 295, 67, 191, 190, 136, 137, 201, 9, 66, 172, 69, 50, 149, 70,
    198, 139, 322, 300, 120, 64, 63, 5, 97, 72, 123, 188, 221,
})


def list_rank(lc_number: int | None) -> float | None:
    """Sprint priority: 1.0 for Hot 100, 0.5 for Top Interview 150 only, None if in neither."""
    if lc_number in HOT_100:
        return 1.0
    if lc_number in TOP_INTERVIEW_150:
        return 0.5
    return None


def get_plan(plan_id: str | None) -> Plan:
    return PLANS.get(plan_id or DEFAULT_PLAN, PLANS[DEFAULT_PLAN])
