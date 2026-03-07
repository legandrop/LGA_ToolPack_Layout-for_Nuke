from pathlib import Path
import re
import shutil
from PIL import Image

DOC_DIR = Path(__file__).resolve().parent
PANDOC_MD = DOC_DIR / 'LGA_LayoutToolPack_pandoc.md'
FINAL_MD = DOC_DIR / 'LGA_LayoutToolPack.md'
SRC_MEDIA = DOC_DIR / 'media' / 'media'
DEST_MEDIA = DOC_DIR / 'media_md'
LOG_PATH = DOC_DIR / 'scale_images.log'

if not PANDOC_MD.exists():
    raise SystemExit("Missing LGA_LayoutToolPack_pandoc.md. Run pandoc with --extract-media=media_tmp to regenerate metadata before scaling.")
if not SRC_MEDIA.exists():
    raise SystemExit("Missing media/media/ with the high-res exports. Run pandoc with --extract-media=media first.")

text = PANDOC_MD.read_text(encoding='utf-8')
size_map = {}
pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)\{([^}]*)\}')
for match in pattern.finditer(text):
    path = match.group(1)
    filename = Path(path).name
    attrs = match.group(2)
    width = height = None
    m_w = re.search(r'width="([0-9\.]+)in"', attrs)
    if m_w:
        width = float(m_w.group(1))
    m_h = re.search(r'height="([0-9\.]+)in"', attrs)
    if m_h:
        height = float(m_h.group(1))
    entry = size_map.setdefault(filename, {})
    if width is not None:
        entry['width_in'] = width
    if height is not None:
        entry['height_in'] = height

final_text = FINAL_MD.read_text(encoding='utf-8')
img_pattern = re.compile(r'!\[[^\]]*\]\((media/media/([^\)]+))\)')
files = []
for match in img_pattern.finditer(final_text):
    files.append(match.group(2))
unique_files = sorted(set(files))

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
        entry = size_map.get(fname, {})
        width_in = entry.get('width_in')
        if width_in is None:
            target_w = orig_w
        else:
            target_w = max(1, int(round(width_in * 96)))
        target_h = max(1, int(round(orig_h * target_w / orig_w)))
        if (target_w, target_h) == (orig_w, orig_h):
            resized = img.copy()
        else:
            resized = img.resize((target_w, target_h), Image.LANCZOS)
        dest = DEST_MEDIA / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dest)
        report_lines.append(f"{fname}: {orig_w}x{orig_h} -> {target_w}x{target_h}")

FINAL_MD.write_text(final_text.replace('media/media/', 'media_md/'), encoding='utf-8')
LOG_PATH.write_text('\n'.join(report_lines), encoding='utf-8')
print(f"Scaled {len(unique_files)} images. Details -> {LOG_PATH.name}")
