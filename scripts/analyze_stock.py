#!/usr/bin/env python3
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.index import analyze_stock, _dataclass_to_dict

code = sys.argv[1] if len(sys.argv) > 1 else "600519"
result = asyncio.run(analyze_stock(code))
print(json.dumps(_dataclass_to_dict(result), ensure_ascii=False, indent=2))
