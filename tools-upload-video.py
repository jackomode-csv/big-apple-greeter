#!/usr/bin/env python
"""Push assets/*.mp4 to the Cloudflare R2 bucket that serves the site's reels.

    set R2_ACCOUNT_ID=...            (Cloudflare account id)
    set R2_ACCESS_KEY_ID=...         (R2 API token, "Object Read & Write")
    set R2_SECRET_ACCESS_KEY=...
    python tools-upload-video.py             # dry run, changes nothing
    python tools-upload-video.py --go        # actually upload
    python tools-upload-video.py --check     # compare local against the bucket

Only video moves, and only the web encodes. assets/_web/ holds the versions
built for delivery (48MB across 13 clips); the masters beside them in assets/
are 205MB and stay on this machine. The 35 images under assets/ are committed
to the repo and stay there. Once these are up, render with the bucket's public
URL and the pages point at it:

    python tools-render.py --base https://<public-host> volunteers-v2

Credentials are read from the environment and handed to rclone through its own
RCLONE_CONFIG_* variables, so they never appear in a command line, in a config
file on disk, or in this repo.
"""
import os, re, subprocess, sys, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
BUCKET = 'big-apple-greeter-content'
REMOTE = 'R2'
CACHE = 'public, max-age=604800'      # a week. Rename a clip to bust it.

RCLONE_CANDIDATES = [
    'rclone',
    os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links\rclone.exe'),
    os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages'
                       r'\Rclone.Rclone_Microsoft.Winget.Source_8wekyb3d8bbwe'
                       r'\rclone-v1.75.1-windows-amd64\rclone.exe'),
]


def rclone():
    for c in RCLONE_CANDIDATES:
        try:
            subprocess.run([c, 'version'], capture_output=True, check=True)
            return c
        except Exception:
            continue
    sys.exit('rclone not found. winget install Rclone.Rclone')


def env():
    need = ['R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY']
    missing = [n for n in need if not os.environ.get(n)]
    if missing:
        sys.exit('missing environment variable(s): %s\n\n'
                 'Cloudflare dashboard -> R2 -> Manage API tokens -> Create token,\n'
                 'permission "Object Read & Write", scoped to %s.\n'
                 'The account id sits on the R2 overview page.'
                 % (', '.join(missing), BUCKET))
    e = dict(os.environ)
    e.update({
        'RCLONE_CONFIG_%s_TYPE' % REMOTE: 's3',
        'RCLONE_CONFIG_%s_PROVIDER' % REMOTE: 'Cloudflare',
        'RCLONE_CONFIG_%s_ACCESS_KEY_ID' % REMOTE: os.environ['R2_ACCESS_KEY_ID'],
        'RCLONE_CONFIG_%s_SECRET_ACCESS_KEY' % REMOTE: os.environ['R2_SECRET_ACCESS_KEY'],
        'RCLONE_CONFIG_%s_ENDPOINT' % REMOTE:
            'https://%s.r2.cloudflarestorage.com' % os.environ['R2_ACCOUNT_ID'],
        'RCLONE_CONFIG_%s_NO_CHECK_BUCKET' % REMOTE: 'true',
    })
    return e


def referenced():
    """Which clips the site actually asks for, so orphans are visible."""
    want = set()
    for p in glob.glob(os.path.join(ROOT, '*.html')):
        if os.path.basename(p) == 'big-apple-greeter-SHARE.html':
            continue            # the base64 bundle references everything
        s = open(p, encoding='utf-8', errors='ignore').read()
        want |= set(re.findall(r'assets/([\w.\-]+\.mp4)', s))
    return want


def main():
    go = '--go' in sys.argv
    check = '--check' in sys.argv
    rc, e = rclone(), env()
    src = os.path.join(ROOT, 'assets', '_web')
    if not os.path.isdir(src):
        sys.exit('assets/_web not found. That folder holds the web encodes; the masters beside them are 4x larger and are not what ships.')
    dst = '%s:%s/' % (REMOTE, BUCKET)

    files = sorted(glob.glob(os.path.join(src, '*.mp4')))
    want = referenced()
    total = sum(os.path.getsize(f) for f in files)
    print('%d clips, %.1f MB -> %s\n' % (len(files), total / 1048576.0, dst))
    for f in files:
        n = os.path.basename(f)
        print('  %-28s %8.2f MB  %s'
              % (n, os.path.getsize(f) / 1048576.0,
                 '' if n in want else '(not referenced by any page)'))
    orphan_refs = want - set(os.path.basename(f) for f in files)
    if orphan_refs:
        print('\n  MISSING LOCALLY, but referenced: %s' % ', '.join(sorted(orphan_refs)))

    cmd = [rc, 'check' if check else 'copy', src, dst,
           '--include', '*.mp4', '--transfers', '4',
           # fail fast on a bad key or endpoint instead of retrying for minutes
           '--retries', '2', '--low-level-retries', '3',
           '--contimeout', '15s', '--timeout', '60s']
    if go:
        cmd.append('--progress')
    if not check:
        cmd += ['--header-upload', 'Cache-Control: ' + CACHE]
    if not go and not check:
        cmd.append('--dry-run')
        print('\nDRY RUN. Nothing is uploaded. Add --go to do it for real.\n')
    print('\n$ rclone %s ...\n' % cmd[1])
    sys.exit(subprocess.call(cmd, env=e))


if __name__ == '__main__':
    main()
