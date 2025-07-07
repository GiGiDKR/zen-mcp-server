import asyncio
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_file)
    print("✅ Fichier .env chargé")
except ImportError:
    print("❌ dotenv non disponible")

# Initialize providers (necessary for standalone tool usage)
from server import configure_providers

try:
    configure_providers()
    print("✅ Providers configurés")
except Exception as e:
    print(f"❌ Erreur configuration providers: {e}")

from tools.chat import ChatTool


async def main():
    tool = ChatTool()
    arguments = {"prompt": "Donne-moi un exemple de décorateur Python.", "persona_id": "python_expert"}
    result = await tool.execute(arguments)
    for r in result:
        print(r.text)


if __name__ == "__main__":
    asyncio.run(main())
