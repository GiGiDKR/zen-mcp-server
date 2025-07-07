"""
Test basique pour vérifier que nos outils personas fonctionnent.
"""

import asyncio
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.tools import PersonasCreateTool, PersonasListTool


async def test_personas_tools():
    """Test basique des outils personas"""
    print("Testing Personas Tools...")

    # Test PersonasListTool
    print("\n1. Testing PersonasListTool...")
    list_tool = PersonasListTool()
    print(f"Tool name: {list_tool.get_name()}")
    print(f"Description: {list_tool.get_description()[:100]}...")

    # Test PersonasCreateTool
    print("\n2. Testing PersonasCreateTool...")
    create_tool = PersonasCreateTool()
    print(f"Tool name: {create_tool.get_name()}")
    print(f"Description: {create_tool.get_description()[:100]}...")

    # Test tool fields
    print("\n3. Testing tool fields...")
    create_fields = create_tool.get_tool_fields()
    print(f"Create tool has {len(create_fields)} fields: {list(create_fields.keys())}")

    list_fields = list_tool.get_tool_fields()
    print(f"List tool has {len(list_fields)} fields: {list(list_fields.keys())}")

    print("\n✅ Basic personas tools test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_personas_tools())
