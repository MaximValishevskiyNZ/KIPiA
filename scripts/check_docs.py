#!/usr/bin/env python3
"""Check local documentation integrity; no network requests or dependencies."""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    counts = {'markdown': 0, 'links': 0, 'svg': 0, 'json': 0}
    for file in ROOT.rglob('*'):
        if not file.is_file() or '.git' in file.parts:
            continue
        relative = file.relative_to(ROOT)
        if file.suffix == '.md':
            counts['markdown'] += 1
            content = file.read_text()
            body = re.sub(r'```[^\n]*\n.*?```', '', content, flags=re.S)
            if len(re.findall(r'^# ', body, flags=re.M)) != 1:
                errors.append(f'{relative}: expected one H1')
            destinations = re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', body)
            destinations += re.findall(r'(?:src|href)="([^"]+)"', body)
            for value in destinations:
                counts['links'] += 1
                url = urlsplit(value.strip('<>'))
                if url.scheme or not url.path:
                    continue
                target = (file.parent / unquote(url.path)).resolve()
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f'{relative}: missing local target {value}')
        elif file.suffix == '.svg':
            counts['svg'] += 1
            try:
                root = ET.fromstring(file.read_text())
                ns = {'s': 'http://www.w3.org/2000/svg'}
                if root.find('s:title', ns) is None or root.find('s:desc', ns) is None:
                    errors.append(f'{relative}: missing accessible title/description')
            except ET.ParseError as error:
                errors.append(f'{relative}: {error}')
        elif file.suffix == '.json':
            counts['json'] += 1
            try:
                data = json.loads(file.read_text())
                if file.name == 'sources.json':
                    seen = set()
                    for source in data['documents']:
                        if urlsplit(source['url']).hostname not in {'www.endress.com', 'bdih-download.endress.com'}:
                            errors.append(f'{relative}: non-official source domain')
                        if not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
                            errors.append(f'{relative}: invalid SHA-256')
                        if source['source_id'] in seen:
                            errors.append(f'{relative}: duplicate source ID')
                        seen.add(source['source_id'])
            except (ValueError, KeyError) as error:
                errors.append(f'{relative}: {error}')
    for error in errors:
        print('ERROR:', error)
    print('Checked:', ', '.join(f'{n} {kind}' for kind, n in counts.items()))
    if errors:
        return 1
    print('Local links, source manifest, JSON and accessible SVG: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
