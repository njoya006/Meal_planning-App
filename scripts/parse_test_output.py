import sys
from pathlib import Path
p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('temp_billing_test_output6.txt')
if not p.exists():
    print('file not found:', p)
    sys.exit(1)
lines = p.read_text(errors='replace').splitlines()
# Print lines that include test summary keywords
for l in lines:
    if 'Ran ' in l or l.strip() == 'OK' or 'FAILED' in l:
        print(l)
# Print a separator and the last 40 lines for context
print('\n--- tail (last 40 lines) ---')
for l in lines[-40:]:
    print(l)
