"""Credential-free, syscall/resource restricted raster converter. Runs separately."""
import base64
import ctypes
import io
import json
import math
import resource
import sys
import warnings

MIB = 1024 * 1024
resource.setrlimit(resource.RLIMIT_AS, (192 * MIB, 192 * MIB))
resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
resource.setrlimit(resource.RLIMIT_FSIZE, (6 * MIB, 6 * MIB))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from PIL import Image
import pypdfium2 as pdfium
# Load plugins before prohibiting filesystem access; no untrusted content parsed yet.
Image.init()
Image.MAX_IMAGE_PIXELS = 8_000_000
warnings.simplefilter('error', Image.DecompressionBombWarning)
raw = sys.stdin.buffer.read(10 * MIB + 1)
if len(raw) > 10 * MIB:
    sys.exit(1)


def restrict():
    if sys.platform != 'linux':
        raise RuntimeError('Linux sandbox required')
    lib = ctypes.CDLL('libseccomp.so.2')
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    context = lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW; resources already limited.
    if not context:
        raise RuntimeError('Sandbox unavailable')
    try:
        for name in ('open', 'openat', 'openat2', 'creat', 'socket', 'socketpair', 'connect', 'bind',
                     'listen', 'accept', 'accept4', 'execve', 'execveat', 'fork', 'vfork', 'clone',
                     'clone3', 'ptrace', 'process_vm_readv', 'process_vm_writev', 'mount', 'umount2',
                     'io_uring_setup', 'unlink', 'unlinkat', 'rename', 'renameat', 'renameat2'):
            number = lib.seccomp_syscall_resolve_name(name.encode())
            if number >= 0 and lib.seccomp_rule_add(context, 0x00050001, number, 0) != 0:
                raise RuntimeError('Sandbox failed')
        if lib.seccomp_load(context) != 0:
            raise RuntimeError('Sandbox failed')
    finally:
        lib.seccomp_release(context)


def encoded(image):
    image = image.convert('RGB')
    image.thumbnail((1200, 1200))
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=80, optimize=False)
    if output.tell() > MIB:
        raise ValueError('Raster limit')
    return {'data_url': 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode(),
            'width': image.width, 'height': image.height}


try:
    restrict()
    if sys.argv[1] == 'pdf':
        with pdfium.PdfDocument(raw) as document:
            total = len(document)
            if total < 1:
                raise ValueError('Empty PDF')
            images = []
            for number in range(min(total, 6)):
                page = document[number]
                width, height = page.get_size()
                if not all(math.isfinite(n) and 0 < n < 100000 for n in (width, height)):
                    raise ValueError('Page dimensions')
                bitmap = page.render(scale=min(1.5, 1000 / max(width, height)), draw_annots=False)
                pil = bitmap.to_pil()
                images.append(encoded(pil))
                pil.close()
                bitmap.close()
                page.close()
            result = {'kind': 'pdf', 'images': images, 'total_pages': total, 'truncated': total > 6}
    else:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('PNG', 'JPEG', 'WEBP') or image.width * image.height > 8_000_000:
                raise ValueError('Unsupported image')
            image.load()
            result = {'kind': 'image', 'images': [encoded(image)],
                      'truncated': getattr(image, 'n_frames', 1) > 1}
    payload = json.dumps(result)
    if len(payload) > 5 * MIB:
        raise ValueError('Preview limit')
    sys.stdout.write(payload)
except Exception:
    # Never return parser error text or paths from potentially malicious content.
    sys.exit(1)
