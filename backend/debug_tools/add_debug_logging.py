"""
Add debug logging to text_parser.py to see if PyMuPDF fonts are being used
"""
import sys
from pathlib import Path

# Read the file
file_path = Path(__file__).parent.parent / "services/xml_parser/extractors/text_parser.py"

with open(file_path, 'r') as f:
    content = f.read()

# Add debug logging after line 59 (if font_info:)
lines = content.split('\n')

# Find the line with "if font_info:"
for i, line in enumerate(lines):
    if 'if font_info:' in line and 'Use PyMuPDF font information' in lines[i+1]:
        # Insert debug logging
        indent = '                    '
        debug_lines = [
            f"{indent}# DEBUG: PyMuPDF font found!",
            f"{indent}print(f'[DEBUG] PyMuPDF font for \"{{clean_text[:30]}}...\": {{font_info.font_size:.2f}}pt → {{font_info.font_size * 1.333 * zoom_factor:.2f}}px')"
        ]
        lines.insert(i+1, '\n'.join(debug_lines))
        break

# Find the line with "if not font_spec:" (fallback)
for i, line in enumerate(lines):
    if 'Fallback to pdftohtml fontspec if PyMuPDF' in line:
        # Insert debug logging
        indent = '            '
        debug_line = f"{indent}print(f'[DEBUG] Using pdftohtml fallback for \"{{clean_text[:30]}}...\"')"
        lines.insert(i+2, debug_line)
        break

# Write back
with open(file_path, 'w') as f:
    f.write('\n'.join(lines))

print("✅ Debug logging added to text_parser.py")
print("Run the test again to see which fonts are being used.")
