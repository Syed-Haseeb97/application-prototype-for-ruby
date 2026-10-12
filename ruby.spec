# PyInstaller spec for Ruby.  Build on Windows:  pyinstaller --noconfirm ruby.spec
# NOTE: written but NOT executed in the authoring environment (no Windows / PyInstaller).
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [("assets", "assets"), (".env.example", ".")]
datas += collect_data_files("speech_recognition")      # bundled flac converter
datas += collect_data_files("edge_tts")
datas += collect_data_files("google.generativeai", include_py_files=False)

hiddenimports = (
    collect_submodules("pynput")
    + collect_submodules("google.generativeai")
    + ["pyaudiowpatch", "pyttsx3.drivers", "pyttsx3.drivers.sapi5", "PyQt6.QtNetwork"]
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "prototypes"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Ruby",
    icon="assets/ruby.ico",
    console=False,          # no terminal window
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Ruby")
