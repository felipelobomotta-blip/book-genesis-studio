# Build with: python -m PyInstaller packaging/book_genesis_studio.spec --noconfirm
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).parent
data = [(str(root / 'runner/web'), 'runner/web'), (str(root / 'runner/config'), 'runner/config')]
data += [(str(root / name), 'runner/data/' + name) for name in ('agents', 'knowledge', 'skills')]
analysis = Analysis([str(root / 'packaging/studio_entry.py')], pathex=[str(root)], binaries=[], datas=data,
                    hiddenimports=collect_submodules('runner'), hookspath=[], runtime_hooks=[],
                    excludes=['IPython', 'jupyter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'torch', 'tensorflow', 'pygame', 'cv2', 'PIL', 'pytest'])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='BookGenesis', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False)
collect = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name='BookGenesis')
