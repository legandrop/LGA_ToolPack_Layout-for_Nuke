from pathlib import Path
import re
import shutil
from PIL import Image

DOC_DIR = Path(__file__).resolve().parent
ROOT_DIR = DOC_DIR.parent
PANDOC_MD = DOC_DIR / 'LGA_LayoutToolPack_pandoc.md'
FINAL_MD = ROOT_DIR / 'README.md'
SRC_MEDIA = ROOT_DIR / 'Doc_Media' / 'Originals'
DEST_MEDIA = ROOT_DIR / 'Doc_Media'
LOG_PATH = DOC_DIR / 'scale_images.log'
ADJUSTMENTS = {
    # fine-tune specific icons (extra padding, etc.)
    'seccion_azul.png': {'bottom_pad': 5},
    'seccion_amarilla.png': {'bottom_pad': 5},
    'seccion_verde.png': {'bottom_pad': 5},
    'seccion_naranja.png': {'bottom_pad': 5},
    'seccion_violeta.png': {'bottom_pad': 5},
    'seccion_rosa.png': {'bottom_pad': 5},
}
ALWAYS_INCLUDE = {'image22.png'}
ICON_ALIASES = {
    'seccion_azul.png': 'image15.png',
    'seccion_amarilla.png': 'image4.png',
    'seccion_verde.png': 'image6.png',
    'seccion_naranja.png': 'image16.png',
    'seccion_violeta.png': 'image28.png',
    'seccion_rosa.png': 'image3.png',
}

if not PANDOC_MD.exists():
    raise SystemExit("Missing LGA_LayoutToolPack_pandoc.md. Run pandoc with --extract-media=media_tmp to regenerate metadata before scaling.")
if not SRC_MEDIA.exists():
    raise SystemExit("Missing Doc_Media/Originals/ with the high-res exports. Run pandoc with --extract-media then copy the assets there.")

text = PANDOC_MD.read_text(encoding='utf-8')
size_map = {}
pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)\{([^}]*)\}')
for match in pattern.finditer(text):
    path = match.group(1)
    filename = Path(path).name
    attrs = match.group(2)
    width = height = None
    m_w = re.search(r'width="([0-9eE\.\-]+)in"', attrs)
    if m_w:
        width = float(m_w.group(1))
    m_h = re.search(r'height="([0-9eE\.\-]+)in"', attrs)
    if m_h:
        height = float(m_h.group(1))
    entry = size_map.setdefault(filename, {})
    if width is not None:
        entry['width_in'] = width
    if height is not None:
        entry['height_in'] = height

final_text = FINAL_MD.read_text(encoding='utf-8')
files = []
img_pattern = re.compile(r'!\[[^\]]*\]\((Doc_Media/([^\)]+))\)')
for match in img_pattern.finditer(final_text):
    files.append(match.group(2))
html_pattern = re.compile(r'src="Doc_Media/([^"]+)"')
for match in html_pattern.finditer(final_text):
    files.append(match.group(1))
unique_files = sorted(set(files) | ALWAYS_INCLUDE)

if DEST_MEDIA.exists():
    shutil.rmtree(DEST_MEDIA)
DEST_MEDIA.mkdir(parents=True, exist_ok=True)

report_lines = []
for fname in unique_files:
    src = SRC_MEDIA / fname
    if not src.exists():
        report_lines.append(f"SKIP {fname} (missing source)")
        continue
    with Image.open(src) as img:
        orig_w, orig_h = img.size
        lookup_name = ICON_ALIASES.get(fname, fname)
        entry = size_map.get(lookup_name, {})
        width_in = entry.get('width_in')
        height_in = entry.get('height_in')
        if width_in is not None:
            target_w = max(1, int(round(width_in * 96)))
        else:
            target_w = orig_w
        if height_in is not None:
            target_h = max(1, int(round(height_in * 96)))
            if width_in is None:
                target_w = max(1, int(round(orig_w * target_h / orig_h)))
        else:
            target_h = max(1, int(round(orig_h * target_w / orig_w)))
        if (target_w, target_h) == (orig_w, orig_h):
            resized = img.copy()
        else:
            resized = img.resize((target_w, target_h), Image.LANCZOS)
        final_w, final_h = resized.size
        adjustments = ADJUSTMENTS.get(fname, {})
        bottom_pad = adjustments.get('bottom_pad', 0)
        if bottom_pad:
            rgba = resized.convert('RGBA')
            padded = Image.new('RGBA', (final_w, final_h + bottom_pad), (0, 0, 0, 0))
            padded.paste(rgba, (0, 0))
            resized = padded
            final_w, final_h = resized.size
        dest = DEST_MEDIA / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dest)
        report_lines.append(f"{fname}: {orig_w}x{orig_h} -> {final_w}x{final_h}")

LOG_PATH.write_text('\n'.join(report_lines), encoding='utf-8')
print(f"Scaled {len(unique_files)} images. Details -> {LOG_PATH.name}")
