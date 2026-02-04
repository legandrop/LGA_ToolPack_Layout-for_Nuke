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


def example_merge_graph() -> Graph:
    g = Graph()
    g.principal_column = "A"

    # Principal column (Grades + Merges)
    main = [
        ("Grade1", 12.0),
        ("Grade2", 11.0),
        ("Grade3", 10.0),
        ("Grade4", 9.0),
        ("Grade5", 8.0),
        ("Grade6", 6.0),
        ("Grade7", 5.0),
        ("Grade8", 4.0),
        ("Grade9", 3.0),
        ("Grade10", 2.0),
        ("Merge1", 1.0),
        ("Grade11", 0.0),
        ("Merge2", -2.0),
        ("Grade12", -3.0),
        ("Grade13", -4.0),
        ("Grade14", -5.0),
    ]
    for idx, (name, y) in enumerate(main):
        color = "#6b78d6" if name.startswith("Merge") else "#cbd6ee"
        g.add_node(Node(name=name, column="A", order=idx, x=0.0, y=y, height=0.5))

    # Right column (upper)
    right_upper = [
        ("Roto2", 13.0, 0.5),
        ("Blur2", 11.5, 0.5),
        ("Copy1", 10.0, 0.5),
        ("Roto1", 8.5, 0.5),
        ("Blur1", 7.0, 0.5),
        ("Dot1", 6.0, 0.2),
    ]
    for idx, (name, y, h) in enumerate(right_upper):
        g.add_node(Node(name=name, column="B", order=idx, x=6.0, y=y, height=h))

    # Right column (lower)
    right_lower = [
        ("Roto3", 3.0, 0.5),
        ("Blur3", 1.5, 0.5),
        ("Dot2", 1.0, 0.2),
    ]
    for idx, (name, y, h) in enumerate(right_lower):
        g.add_node(Node(name=name, column="C", order=idx, x=6.0, y=y, height=h))

    # Left column (upper) - same column name to form two subgroups
    left_upper = [
        ("Grade15", 9.0),
        ("Grade16", 8.0),
        ("Grade17", 1.0),  # aligned to Merge1 (A input)
    ]
    for idx, (name, y) in enumerate(left_upper):
        g.add_node(Node(name=name, column="L", order=idx, x=-6.0, y=y, height=0.5))

    # Left column (lower) - same column, separate subgroup (no connection to upper)
    left_lower = [
        ("Grade18", -0.5),
        ("Grade19", -1.5),
        ("Grade20", -2.5),
        ("Grade21", -2.0),  # aligned to Merge2 (A input)
    ]
    for idx, (name, y) in enumerate(left_lower):
        g.add_node(Node(name=name, column="L", order=len(left_upper) + idx, x=-6.0, y=y, height=0.5))

    # Flow edges (main)
    for a, b in zip(main[:-1], main[1:]):
        g.add_edge(Edge(a[0], b[0]))

    # Flow edges (side columns)
    g.add_edge(Edge("Roto2", "Blur2"))
    g.add_edge(Edge("Blur2", "Copy1"))
    g.add_edge(Edge("Roto1", "Blur1"))
    g.add_edge(Edge("Blur1", "Dot1"))

    g.add_edge(Edge("Roto3", "Blur3"))
    g.add_edge(Edge("Blur3", "Dot2"))

    g.add_edge(Edge("Grade15", "Grade16"))
    g.add_edge(Edge("Grade16", "Grade17"))
    g.add_edge(Edge("Grade18", "Grade19"))
    g.add_edge(Edge("Grade19", "Grade20"))
    g.add_edge(Edge("Grade20", "Grade21"))

    # Alignment constraints (mask)
    g.add_edge(Edge("Grade3", "Copy1", kind="mask", align=True))
    g.add_edge(Edge("Dot1", "Grade6", kind="mask", align=True))
    g.add_edge(Edge("Dot2", "Merge1", kind="mask", align=True))

    # Extra connections (A inputs)
    g.add_edge(Edge("Grade17", "Merge1", kind="A", align=True))
    g.add_edge(Edge("Grade21", "Merge2", kind="A", align=True))

    return g
