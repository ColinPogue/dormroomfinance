"""Verify the new automatic-article disclosure using a disposable, unpublished Hugo fixture."""
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fixture=ROOT/'content/posts/drf-automatic-render-test.md'
if fixture.exists():raise RuntimeError('Refusing to replace an existing fixture path')
try:
 fixture.write_text('''---
title: "Automatic article rendering test"
date: 2026-11-12T00:00:00Z
description: "Unpublished validation fixture"
categories: ["Budgeting"]
draft: false
automated: true
sourceChecked: 2026-11-12
---
## Example section

This temporary fixture checks rendering and is never included in a public release.
''')
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['hugo','--source',str(ROOT),'--destination',tmp,'--minify'],check=True,capture_output=True)
  html=(Path(tmp)/'posts/drf-automatic-render-test/index.html').read_text()
  assert 'Published automatically.' in html
  assert 'Articles use automated research and checks.' in html
  assert 'not individually reviewed' not in html
  assert 'From the archive.' not in html
  assert html.count('<h1')==1
 print('Automatic article rendering and truthful disclosure passed.')
finally:fixture.unlink(missing_ok=True)
