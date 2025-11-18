import sys, os, traceback
OUT = '/tmp/rag_integration_result.txt'
# clear
try:
    if os.path.exists(OUT):
        os.remove(OUT)
except Exception:
    pass

def write(s):
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write(s + '\n')

write('Python: ' + sys.executable)
# ensure rag package dir is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
write('sys.path[0] = ' + sys.path[0])
try:
    import rag.integration as ri
    write('imported rag.integration: ' + repr(ri))
except Exception:
    with open(OUT, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    write('import failed; see traceback above')
