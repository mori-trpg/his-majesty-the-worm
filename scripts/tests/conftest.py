import sys
from pathlib import Path

# 讓 tests 能 import scripts/ 下的模組
sys.path.insert(0, str(Path(__file__).parent.parent))
