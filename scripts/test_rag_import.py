import importlib, traceback, sys, os

OUT_PATH = '/tmp/rag_import_result.txt'

def write(msg: str):
    with open(OUT_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# Clear previous output
try:
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)
except Exception:
    pass

write(f'Python executable: {sys.executable}')
try:
    m = importlib.import_module('aimemos.services.chat')
    write('imported aimemos.services.chat')
    write(f'RAG_AVAILABLE = {getattr(m, "RAG_AVAILABLE", None)}')
    write(f'_rag_import_error = {repr(getattr(m, "_rag_import_error", None))}')
except Exception:
    # Capture full traceback to file
    with open(OUT_PATH, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    write('Import failed (traceback written above)')
