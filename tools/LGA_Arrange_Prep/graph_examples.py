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
        height = 0.8 if name.startswith("Merge") else (0.6 if name in ("Grade3", "Grade11") else 0.5)
        g.add_node(Node(name=name, column="A", order=idx, x=0.0, y=y, height=height))

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

    # Right column (lower) - same column name to form two subgroups
    right_lower = [
        ("Roto3", 3.0, 0.5),
        ("Blur3", 1.5, 0.5),
        ("Dot2", 1.0, 0.28),
    ]
    for idx, (name, y, h) in enumerate(right_lower):
        g.add_node(Node(name=name, column="B", order=len(right_upper) + idx, x=6.0, y=y, height=h))

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


def example_complex_graph() -> Graph:
    g = Graph()
    g.principal_column = "A"

    # Principal column (A)
    main = [
        ("GradeA1", 18.0),
        ("GradeA2", 16.5),
        ("GradeA3", 15.0),
        ("GradeA4", 13.6),
        ("GradeA5", 12.2),
        ("GradeA6", 10.8),
        ("GradeA7", 9.2),
        ("GradeA8", 7.7),
        ("MergeA", 6.0),
        ("GradeA9", 4.2),
        ("GradeA10", 3.1),
        ("GradeA11", 1.8),
        ("MergeB", 0.6),
        ("GradeA12", -1.0),
        ("GradeA13", -2.2),
        ("GradeA14", -3.5),
        ("GradeA15", -5.0),
    ]
    for idx, (name, y) in enumerate(main):
        x = 0.0 + (0.2 if idx % 2 == 0 else -0.15)  # slight x jitter
        height = 0.8 if name.startswith("Merge") else (0.7 if name in ("GradeA4", "GradeA9") else 0.5)
        g.add_node(Node(name=name, column="A", order=idx, x=x, y=y, height=height))

    # Left column (L) with two subgroups
    left = [
        ("GradeL1", 14.8),
        ("GradeL2", 13.4),
        ("GradeL3", 6.0),   # aligns to MergeA
        ("GradeL4", -0.4),
        ("GradeL5", -1.6),  # aligns to MergeB
    ]
    for idx, (name, y) in enumerate(left):
        x = -7.2 + (0.15 if idx % 2 == 0 else -0.1)
        height = 0.6 if name == "GradeL2" else 0.5
        g.add_node(Node(name=name, column="L", order=idx, x=x, y=y, height=height))

    # Right column (R) with two subgroups
    right = [
        ("RotoR1", 17.2),
        ("BlurR1", 15.6),
        ("CopyR1", 13.6),   # aligns to GradeA4
        ("RotoR2", 11.0),
        ("BlurR2", 9.6),
        ("DotR1", 4.2),     # aligns to GradeA9
    ]
    for idx, (name, y) in enumerate(right):
        x = 7.1 + (0.1 if idx % 2 == 0 else -0.12)
        h = 0.3 if name.startswith("Dot") else (0.9 if name.startswith("Copy") else 0.6)
        g.add_node(Node(name=name, column="R", order=idx, x=x, y=y, height=h))

    # Extra far-right column (RR)
    far_right = [
        ("RotoRR1", 12.8),
        ("BlurRR1", 11.2),
        ("DotRR1", 0.6),    # aligns to MergeB
    ]
    for idx, (name, y) in enumerate(far_right):
        x = 10.5 + (0.2 if idx % 2 == 0 else -0.15)
        h = 0.25 if name.startswith("Dot") else 0.7
        g.add_node(Node(name=name, column="RR", order=idx, x=x, y=y, height=h))

    # Flow edges main column
    for a, b in zip(main[:-1], main[1:]):
        g.add_edge(Edge(a[0], b[0]))

    # Flow edges left column (two subgroups, no link between L3 and L4)
    g.add_edge(Edge("GradeL1", "GradeL2"))
    g.add_edge(Edge("GradeL2", "GradeL3"))
    g.add_edge(Edge("GradeL4", "GradeL5"))

    # Flow edges right column (two subgroups, no link between CopyR1 and RotoR2)
    g.add_edge(Edge("RotoR1", "BlurR1"))
    g.add_edge(Edge("BlurR1", "CopyR1"))
    g.add_edge(Edge("RotoR2", "BlurR2"))
    g.add_edge(Edge("BlurR2", "DotR1"))

    # Flow edges far-right column
    g.add_edge(Edge("RotoRR1", "BlurRR1"))
    g.add_edge(Edge("BlurRR1", "DotRR1"))

    # Alignment constraints
    g.add_edge(Edge("GradeA4", "CopyR1", kind="mask", align=True))
    g.add_edge(Edge("DotR1", "GradeA9", kind="mask", align=True))
    g.add_edge(Edge("GradeL3", "MergeA", kind="A", align=True))
    g.add_edge(Edge("GradeL5", "MergeB", kind="A", align=True))
    g.add_edge(Edge("DotRR1", "MergeB", kind="mask", align=True))

    return g
