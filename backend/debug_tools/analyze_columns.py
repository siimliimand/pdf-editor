"""
Debug script to analyze horizontal line segments and column positions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import fitz  # PyMuPDF

pdf_path = Path("./temp/test_pdfs/second-page.pdf")

if not pdf_path.exists():
    print(f"PDF not found at {pdf_path}")
    sys.exit(1)

doc = fitz.open(pdf_path)
page = doc[0]

# Get vector graphics
paths = page.get_drawings()

print("=" * 80)
print("HORIZONTAL LINE ANALYSIS")
print("=" * 80)

# Find horizontal lines
h_lines = []
for path in paths:
    for item in path["items"]:
        if item[0] == "l":  # Line
            x0, y0 = item[1]
            x1, y1 = item[2]
            
            # Check if horizontal (y0 ≈ y1)
            if abs(y1 - y0) < 1:
                h_lines.append({
                    'x0': x0,
                    'x1': x1,
                    'y': y0,
                    'width': abs(x1 - x0)
                })

# Group by Y position (within 2px tolerance)
y_groups = {}
for line in h_lines:
    y = line['y']
    found = False
    for group_y in y_groups.keys():
        if abs(y - group_y) < 2:
            y_groups[group_y].append(line)
            found = True
            break
    if not found:
        y_groups[y] = [line]

print(f"\nFound {len(h_lines)} horizontal lines in {len(y_groups)} Y-position groups\n")

# Analyze each group
for y, lines in sorted(y_groups.items()):
    print(f"Y={y:.2f} ({len(lines)} segments):")
    
    # Get all unique X positions
    x_positions = set()
    for line in lines:
        x_positions.add(line['x0'])
        x_positions.add(line['x1'])
    
    x_sorted = sorted(x_positions)
    print(f"  X positions: {[f'{x:.2f}' for x in x_sorted]}")
    
    # Show line segments
    for i, line in enumerate(sorted(lines, key=lambda l: l['x0'])):
        print(f"  Segment {i+1}: x0={line['x0']:.2f}, x1={line['x1']:.2f}, width={line['width']:.2f}")
    print()

# Calculate table boundaries
all_x0 = [line['x0'] for line in h_lines]
all_x1 = [line['x1'] for line in h_lines]
t_left = min(all_x0)
t_right = max(all_x1)
table_width = t_right - t_left

print("=" * 80)
print(f"Table boundaries: left={t_left:.2f}, right={t_right:.2f}, width={table_width:.2f}")
print(f"1% threshold: {table_width * 0.01:.2f}px")
print("=" * 80)

# Collect all unique X positions from line endpoints
all_x_positions = set()
for line in h_lines:
    all_x_positions.add(line['x0'])
    all_x_positions.add(line['x1'])

x_sorted = sorted(all_x_positions)
print(f"\nAll unique X positions ({len(x_sorted)}):")
for i, x in enumerate(x_sorted):
    dist_from_left = x - t_left
    dist_from_right = t_right - x
    print(f"  {i+1}. x={x:.2f} (left+{dist_from_left:.2f}, right-{dist_from_right:.2f})")

doc.close()
