import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rest_framework.exceptions import ValidationError
from .provider import MIB


def raster(raw, kind):
    worker = Path(__file__).with_name('raster_worker.py')
    # Inherited credentials, settings and proxy env are removed. No input path is exposed.
    with tempfile.TemporaryDirectory(prefix='first-raster-') as directory:
        with tempfile.TemporaryFile(dir=directory) as output:
            try:
                result = subprocess.run([sys.executable, '-I', str(worker), kind], input=raw,
                    stdout=output, stderr=subprocess.DEVNULL, cwd=directory,
                    env={'LANG': 'C.UTF-8'}, timeout=12, close_fds=True)
                output.seek(0)
                payload = output.read(5 * MIB + 1)
                if result.returncode != 0 or len(payload) > 5 * MIB:
                    raise ValueError()
                content = json.loads(payload)
                if content.get('kind') != kind:
                    raise ValueError()
                return content
            except (subprocess.TimeoutExpired, OSError, ValueError, TypeError):
                raise ValidationError('Dosya güvenle önizlenemedi. Şifreli/bozuk dosya, 8 megapiksel, süre veya kaynak sınırı olabilir.')


def render(filename, raw):
    suffix = Path(filename).suffix.lower()
    if suffix == '.pdf' and raw.startswith(b'%PDF-'):
        return raster(raw, 'pdf')
    image_magic = (raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'\xff\xd8\xff')
                   or (raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'))
    if suffix in ('.png', '.jpg', '.jpeg', '.webp') and image_magic:
        return raster(raw, 'image')
    if suffix in ('.pdf', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.zip', '.exe', '.dll', '.so', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'):
        raise ValidationError('Bu dosya biçimi veya içeriği desteklenmiyor. Metin, PNG/JPEG/WebP, PDF veya CSV seçin.')
    if len(raw) > MIB:
        raise ValidationError('Metin, Markdown ve CSV dosyaları en çok 1 MiB olabilir.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValidationError('Metin dosyası UTF-8 olmalıdır; bilinmeyen ikili dosyalar desteklenmiyor.')
    if any(ord(c) < 32 and c not in '\r\n\t' for c in text):
        raise ValidationError('İkili dosyalar desteklenmiyor.')
    if suffix == '.csv':
        # CSV never becomes HTML or a downloadable spreadsheet; formulas stay inert strings.
        rows, truncated = [], False
        try:
            for i, row in enumerate(csv.reader(io.StringIO(text))):
                if i >= 200:
                    truncated = True
                    break
                if len(row) > 30 or any(len(cell) > 2000 for cell in row[:30]):
                    truncated = True
                rows.append([cell[:2000] for cell in row[:30]])
        except csv.Error:
            raise ValidationError('CSV çözümlenemedi; alanlar en çok 128 KiB olabilir.')
        return {'kind': 'csv', 'rows': rows, 'truncated': truncated}
    # Markdown is deliberately escaped plain text in v1: no HTML, URLs or asset fetch.
    return {'kind': 'markdown' if suffix in ('.md', '.markdown', '.mdown') else 'text',
            'text': text, 'truncated': False}
