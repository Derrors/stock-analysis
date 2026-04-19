#!/usr/bin/env python3
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.index import analyze_market, _dataclass_to_dict

result = asyncio.run(analyze_market())
print(json.dumps(_dataclass_to_dict(result), ensure_ascii=False, indent=2))
