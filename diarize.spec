import os
from PyInstaller.utils.hooks import collect_data_files
import speechbrain
import lightning_fabric
import pytorch_lightning

datas = []
datas += collect_data_files('pyannote.audio')
datas += collect_data_files('lightning_fabric')
datas += collect_data_files('pytorch_lightning')
datas += collect_data_files('lightning')

# Explicitly bundle complete speechbrain folder so dynamic imports in speechbrain.utils succeed
sb_dir = os.path.dirname(speechbrain.__file__)
datas += [(sb_dir, 'speechbrain')]

# Include version.info files required by lightning
lf_dir = os.path.dirname(lightning_fabric.__file__)
pl_dir = os.path.dirname(pytorch_lightning.__file__)
datas += [(os.path.join(lf_dir, 'version.info'), 'lightning_fabric')]
datas += [(os.path.join(pl_dir, 'version.info'), 'pytorch_lightning')]

hiddenimports = [
    'pyannote.audio.models.segmentation',
    'pyannote.audio.models.embedding',
    'pyannote.audio.pipelines.speaker_diarization',
    'scipy.special.cython_special',
    'sklearn.utils._typedefs',
    'onnxruntime',
    'torch',
    'torchaudio',
]

a = Analysis(
    ['src\\diarize.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='diarize',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    manifest='diarize.manifest',
    icon='assets/ilvi_logo.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='diarize',
)

# --------------------------------------------------------------------------
# Post-build hook: flatten bundle directly into dist/ (no dist/diarize/ folder)
# --------------------------------------------------------------------------
import shutil

built_subfolder = os.path.abspath(coll.name)
target_dist = os.path.dirname(built_subfolder)

if os.path.exists(built_subfolder) and built_subfolder != target_dist:
    for item in os.listdir(built_subfolder):
        src_item = os.path.join(built_subfolder, item)
        dst_item = os.path.join(target_dist, item)
        if os.path.exists(dst_item):
            if os.path.isdir(dst_item):
                shutil.rmtree(dst_item)
            else:
                os.remove(dst_item)
        shutil.move(src_item, dst_item)
    try:
        os.rmdir(built_subfolder)
    except OSError:
        pass


# Clean up temporary PyInstaller build directory (build/diarize)
import atexit

project_root = os.path.dirname(target_dist)
build_dir = os.path.join(project_root, 'build')

def cleanup_build():
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)

# Register at process exit and attempt immediate cleanup
atexit.register(cleanup_build)
cleanup_build()


