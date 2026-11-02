"""Interactive CLI for the Empório da Música agent."""

from src.agent import Agent


BANNER = """
🎸 ───────────────────────────────────────────── 🎸
   Empório da Música — Atendimento Virtual
   (digite 'sair' para encerrar, 'reset' para recomeçar)
🎸 ───────────────────────────────────────────── 🎸
"""


def main():
    print(BANNER)
    agent = Agent()

    while True:
        try:
            user_input = input("\n👤 Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo! 🎵")
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            print("🤖 Bia: Foi um prazer! Volte sempre que precisar 🎶")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("🤖 Bia: Conversa reiniciada. Como posso ajudar?")
            continue

        try:
            reply = agent.send(user_input)
            print(f"\n🤖 Bia: {reply}")
        except Exception as e:
            print(f"\n⚠️  Erro: {e}")


if __name__ == "__main__":
    main()
    