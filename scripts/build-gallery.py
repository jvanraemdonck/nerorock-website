#!/usr/bin/env python3
"""Build the photo gallery.

Scans img/gallery/<folder>/ (one folder per year, e.g. nerorock-2024),
creates small thumbnails in img/gallery-thumbs/<folder>/ and writes the
photo list to js/gallery-data.js, which gallery.html reads.

Run again from the repo root after adding or removing photos:
    python3 scripts/build-gallery.py

Requires cwebp (brew install webp).
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'img' / 'gallery'
THUMBS = ROOT / 'img' / 'gallery-thumbs'
OUT = ROOT / 'js' / 'gallery-data.js'

THUMB_WIDTH = 600
THUMB_QUALITY = 70
EXTENSIONS = {'.webp', '.jpg', '.jpeg', '.png'}


# Years whose file names don't contain the band: group by camera number
# (_DSC1234) or by time in the name (14u14m01s) instead.
# (first, last, group name), both ends inclusive. Filter chips follow the
# order in which names first appear here.
GROUP_RANGES = {
    '2025': [
        ('14u14m01s', '14u41m19s', 'De Ketnetband'),
        ('16u17m22s', '17u22m02s', 'Alice Mae'),
        ('17u22m04s', '17u59m21s', 'Fixkes'),
        ('19u11m41s', '19u36m51s', 'Customs'),
        ('20u36m30s', '21u35m05s', 'Kids with Buns'),
        ('22u22m54s', '23u32m33s', 'Daan'),
        ('15u01m40s', '15u23m37s', 'Sfeer'),
        ('20u23m58s', '20u35m17s', 'Sfeer'),
    ],
    '2022': [
        ('2982', '3214', 'Radio Oorwoud'),
        ('3216', '3368', 'The Ragtime Rumours'),
        ('3400', '3628', 'ILA'),
        ('3633', '3917', 'Guy Swinnen Band'),
        ('3932', '4486', 'School is Cool'),
        ('4496', '4920', 'Yong Yello'),
        ('4967', '5387', 'Yevgueni'),
    ],
}


def natural_key(name):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', name)]


def group_from_ranges(stem, ranges):
    m = re.search(r'^_DSC(\d+)|(\d{2}u\d{2}m\d{2}s)', stem)
    if not m:
        return None
    key = natural_key(m.group(1) or m.group(2))
    for first, last, label in ranges:
        if natural_key(first) <= key <= natural_key(last):
            return label
    return None


def group_for(stem, year):
    """Derive a section name (band / 'Sfeer') from the file name, if it has one."""
    if year in GROUP_RANGES:
        return group_from_ranges(stem, GROUP_RANGES[year])
    # 2021-09-19 - Nerorock 2021 @ Hoeilaart - High Hi - 051
    # 2023-09-17 - Nerorock 2023 @ Hoeilaart - 02. Kapitein Winokio - 001
    m = re.match(r'^\d{4}-\d{2}-\d{2} - .+? @ [^-]+ - (.+) - \d+$', stem)
    if m:
        label = re.sub(r'^\d+\.\s*', '', m.group(1))
    else:
        # Nerorock 2024 - K_s Choice @ Hoeilaart - Jokko - 012
        m = re.match(r'^Nerorock \d{4} - (.+?) @ .+ - \d+$', stem)
        if not m:
            return None
        label = m.group(1)
    label = unicodedata.normalize('NFC', label)  # macOS file names store "ê" as "e" + accent
    label = re.sub(r'(?<=\w)_(?=s\b)', "'", label)  # "K_s Choice" -> "K's Choice"
    label = label.replace('Sfeer, Medewerkers', 'Sfeer & medewerkers')
    label = label.replace('Sfeer - Kindernamiddag', 'Kindernamiddag')
    label = label.replace('Vive La F-ête', 'Vive La Fête')
    return label


def make_thumb(src, dest):
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['cwebp', '-quiet', '-q', str(THUMB_QUALITY), '-resize', str(THUMB_WIDTH), '0',
         '-metadata', 'none', str(src), '-o', str(dest)],
        check=True,
    )


def main():
    years = []
    for folder in sorted(SRC.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        year_match = re.search(r'(\d{4})', folder.name)
        year = year_match.group(1) if year_match else folder.name

        photos = []
        # Configured years keep their configured order (unused names are dropped below)
        groups = list(dict.fromkeys(label for _, _, label in GROUP_RANGES.get(year, [])))
        wanted_thumbs = set()
        for src in sorted(folder.iterdir(), key=lambda p: natural_key(p.name)):
            if src.suffix.lower() not in EXTENSIONS:
                continue
            # Skip Google Drive sync-conflict duplicates
            if 'Exemplaar met conflict' in src.name:
                continue
            thumb = THUMBS / folder.name / (src.stem + '.webp')
            make_thumb(src, thumb)
            wanted_thumbs.add(thumb.name)
            group = group_for(src.stem, year)
            if group and group not in groups:
                groups.append(group)
            # [file name, group index or -1]
            photos.append([src.name, groups.index(group) if group else -1])

        # Remove thumbnails whose original was deleted
        thumb_dir = THUMBS / folder.name
        if thumb_dir.exists():
            for old in thumb_dir.iterdir():
                if old.name not in wanted_thumbs:
                    old.unlink()

        # Drop groups without photos and renumber
        used = sorted({g for _, g in photos if g >= 0})
        photos = [[name, used.index(g) if g >= 0 else -1] for name, g in photos]
        groups = [groups[g] for g in used]

        if photos:
            years.append({'year': year, 'dir': folder.name, 'groups': groups, 'photos': photos})
            print(f'{year}: {len(photos)} foto\'s')

    OUT.write_text(
        '// Generated by scripts/build-gallery.py — do not edit by hand.\n'
        '// Photos: img/gallery/<dir>/<file>, thumbnails: img/gallery-thumbs/<dir>/<file stem>.webp\n'
        'window.GALLERY = ' + json.dumps(years, ensure_ascii=False, separators=(',', ':')) + ';\n',
        encoding='utf-8',
    )
    print(f'Wrote {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
