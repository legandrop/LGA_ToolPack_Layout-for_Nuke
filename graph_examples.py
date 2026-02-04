"""
Example graphs for layout testing (Phase 1).
"""

from layout_core import Graph, Node, Edge


def example_roto_graph() -> Graph:
    g = Graph()
    g.principal_column = "A"

    # Column A (Grades)
    grades = [
        ("Grade1", 10.0),
        ("Grade2", 9.3),
        ("Grade3", 8.6),
        ("Grade4", 7.9),
        ("Grade5", 7.2),
        ("Grade6", 5.6),
        ("Grade7", 4.9),
        ("Grade8", 4.2),
        ("Grade9", 3.5),
        ("Grade10", 2.8),
    ]
    for idx, (name, y) in enumerate(grades):
        g.add_node(Node(name=name, column="A", order=idx, x=0.0, y=y, height=0.5))

    # Column B (Roto/Blur/Copy)
    right = [
        ("Roto2", 10.5, 0.5),
        ("Blur2", 9.3, 0.5),
        ("Copy1", 8.6, 0.5),
        ("Roto1", 7.2, 0.5),
        ("Blur1", 6.4, 0.5),
        ("Dot1", 5.6, 0.2),
    ]
    for idx, (name, y, h) in enumerate(right):
        g.add_node(Node(name=name, column="B", order=idx, x=6.0, y=y, height=h))

    # Flow edges
    g.add_edge(Edge("Grade1", "Grade2"))
    g.add_edge(Edge("Grade2", "Grade3"))
    g.add_edge(Edge("Grade3", "Grade4"))
    g.add_edge(Edge("Grade4", "Grade5"))
    g.add_edge(Edge("Grade5", "Grade6"))
    g.add_edge(Edge("Grade6", "Grade7"))
    g.add_edge(Edge("Grade7", "Grade8"))
    g.add_edge(Edge("Grade8", "Grade9"))
    g.add_edge(Edge("Grade9", "Grade10"))

    g.add_edge(Edge("Roto2", "Blur2"))
    g.add_edge(Edge("Blur2", "Copy1"))
    g.add_edge(Edge("Roto1", "Blur1"))
    g.add_edge(Edge("Blur1", "Dot1"))

    # Alignment constraints (mask connections)
    g.add_edge(Edge("Grade3", "Copy1", kind="mask", align=True))
    g.add_edge(Edge("Dot1", "Grade6", kind="mask", align=True))

    return g

