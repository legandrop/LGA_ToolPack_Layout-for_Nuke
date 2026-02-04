"""
Simple CLI to export example graphs before/after layout.
Usage: python layout_cli.py
"""

from graph_examples import example_roto_graph, example_merge_graph, example_complex_graph
from graphviz_export import to_dot
from layout_core import layout


def main() -> None:
    for label, graph in [
        ("Example1", example_roto_graph()),
        ("Example2", example_merge_graph()),
        ("Example3", example_complex_graph()),
    ]:
        print(f"### {label} BEFORE")
        print(to_dot(graph, title=f"{label}_Before"))

        conflicts = layout(graph, min_gap=0.2)

        print(f"\n### {label} AFTER")
        print(to_dot(graph, title=f"{label}_After"))

        if conflicts:
            print("\n### CONFLICTS")
            for col, (start_idx, end_idx, extra) in conflicts:
                print(f"Column {col}: segment {start_idx}-{end_idx} needs +{extra:.3f} space")
        print("\n")


if __name__ == "__main__":
    main()
