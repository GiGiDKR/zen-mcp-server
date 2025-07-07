#!/usr/bin/env python3
"""
Diagnostic script pour identifier les problèmes d'import du serveur.
"""

import traceback

print("=== DIAGNOSTIC IMPORTS SERVER ===\n")

try:
    print("1. Testing personas tools import...")
    print("✅ Personas tools import OK")
except Exception as e:
    print(f"❌ Personas tools import failed: {e}")
    traceback.print_exc()

try:
    print("\n2. Testing basic tools import...")
    print("✅ Basic tools import OK")
except Exception as e:
    print(f"❌ Basic tools import failed: {e}")
    traceback.print_exc()

try:
    print("\n3. Testing server import...")
    from server import TOOLS

    print(f"✅ Server import OK - Found {len(TOOLS)} tools")

    # Vérifier les personas tools
    personas_tools = [name for name in TOOLS.keys() if "personas" in name]
    print(f"📋 Personas tools found: {personas_tools}")

except Exception as e:
    print(f"❌ Server import failed: {e}")
    traceback.print_exc()

print("\n=== DIAGNOSTIC COMPLETE ===")
