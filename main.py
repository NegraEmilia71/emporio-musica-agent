"""Interactive CLI for the Empório da Música agent Celeste."""

from src.agent import Agent


WELCOME = """
🎸 ───────────────────────────────────────────── 🎸
   Empório da Música — Atendimento Virtual
   Olá! Eu sou a Celeste 🎵
   Hi! I'm Celeste 🎵

   Em que idioma você prefere falar?
   In which language would you like to chat?

   [1] 🇧🇷 Português - Brasil
   [2] 🇺🇸 English
🎸 ───────────────────────────────────────────── 🎸
"""

def ask_language() -> str:
    """Ask the user to pick a language. Returns 'pt' or 'en'."""
    while True:
        try:
            choice = input("\n👉 Digite 1 ou 2 / Type 1 or 2: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo! 🎵")
            raise SystemExit(0)

        if choice in {"1", "pt", "português", "portugues", "br"}:
            return "pt"
        if choice in {"2", "en", "english", "inglês", "ingles"}:
            return "en"

        print("⚠️  Escolha inválida. / Invalid choice. Tente 1 ou 2 / Try 1 or 2.")

def main():
    print(WELCOME)
    language = ask_language()
    agent = Agent(language=language)

    if language == "en":
        goodbye = "🤖 Celeste: It was a pleasure! Come back anytime 🎶"
        reset_msg = "🤖 Celeste: Conversation reset. How can I help?"
        prompt = "\n👤 You: "
        exit_hint = "(type 'exit' to quit, 'reset' to restart)"
    else:
        goodbye = "🤖 Celeste: Foi um prazer! Volte sempre que precisar 🎶"
        reset_msg = "🤖 Celeste: Conversa reiniciada. Como posso ajudar?"
        prompt = "\n👤 Você: "
        exit_hint = "(digite 'sair' para encerrar, 'reset' para recomeçar)"

    print(f"\n💬 {exit_hint}")

    agent = Agent(language=language)

    while True:
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + goodbye.split(": ", 1)[1])
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            print(goodbye)
            break
        if user_input.lower() == "reset":
            agent.reset()
            print(reset_msg)
            continue

        try:
            reply = agent.send(user_input)
            print(f"\n🤖 Celeste: {reply}")
        except Exception as e:
            print(f"\n⚠️  Erro / Error: {e}")


if __name__ == "__main__":
    main()
    