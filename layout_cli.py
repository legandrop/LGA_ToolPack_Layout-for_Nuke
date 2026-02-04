"""
Simple CLI to export example graphs before/after layout.
Usage: python layout_cli.py
"""

from graph_examples import example_roto_graph
from graphviz_export import to_dot
from layout_core import layout


def main() -> None:
    g = example_roto_graph()
    print("### BEFORE")
    print(to_dot(g, title="Before"))

    conflicts = layout(g, min_gap=0.2)

    print("\n### AFTER")
    print(to_dot(g, title="After"))

    if conflicts:
        print("\n### CONFLICTS")
        for col, (start_idx, end_idx, extra) in conflicts:
            print(f"Column {col}: segment {start_idx}-{end_idx} needs +{extra:.3f} space")


if __name__ == "__main__":
    main()

