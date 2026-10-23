
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai.llm_client import LLMClient
from memory.facts_memory import FactsMemory


def main():
    jarvis = LLMClient()
    facts = FactsMemory()
    
    print("JARVIS è online.")
    print("Comandi disponibili:")
    print("  /remember chiave = valore")
    print("  /facts")
    print("  /forget chiave")
    print("  /reset")
    print("  /exit\n")

    while True:
        try:
            message = input("Tu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nJARVIS: Alla prossima.")
            break

        if not message:
            continue

        if message.lower() in {"/exit", "esci", "quit"}:
            print("JARVIS: Alla prossima.")
            break
        if message.lower().strip("?!., ") in {
                    "cosa ti ricordi di me",
                    "che cosa ti ricordi di me",
                    "cosa ricordi di me",
                    "cosa sai di me",
                }:
                    all_facts = facts.get_all()

                    if not all_facts:
                        print("\nJARVIS: Non ho ancora fatti salvati.\n")
                    else:
                        print("\nJARVIS: Ecco cosa ricordo di te:")
                        for key, value in all_facts.items():
                            print(f"- {key}: {value}")
                        print()
                    continue
        domanda = message.lower().strip("?!., ")

        if domanda in {
            "come mi chiamo",
            "qual è il mio nome",
            "qual e il mio nome",
        }:
            nome = facts.get("nome")

            if nome:
                print(f"\nJARVIS: Ti chiami {nome}.\n")
            else:
                print("\nJARVIS: Non conosco ancora il tuo nome.\n")
            continue

        if domanda in {
            "qual è il mio colore preferito",
            "qual e il mio colore preferito",
            "che colore mi piace",
        }:
            colore = facts.get("colore_preferito")

            if colore:
                print(f"\nJARVIS: Il tuo colore preferito è {colore}.\n")
            else:
                print("\nJARVIS: Non conosco ancora il tuo colore preferito.\n")
            continue            
        if message.lower() == "/facts":
            all_facts = facts.get_all()

            if not all_facts:
                print("\nJARVIS: Non ho ancora fatti salvati.\n")
            else:
                print("\nJARVIS: Ecco cosa ricordo:")
                for key, value in all_facts.items():
                    print(f"- {key}: {value}")
                print()
            continue

        if message.startswith("/remember "):
            data = message[len("/remember "):]

            if "=" not in data:
                print(
                    "\nUso corretto: /remember chiave = valore\n"
                )
                continue

            key, value = data.split("=", 1)

            try:
                facts.remember(key, value)
                print(f"\nJARVIS: Ho salvato '{key.strip()}'.\n")
            except ValueError as error:
                print(f"\nErrore: {error}\n")
            continue

        if message.startswith("/forget "):
            key = message[len("/forget "):].strip()

            if not key:
                print("\nUso corretto: /forget chiave\n")
                continue

            if facts.forget(key):
                print(f"\nJARVIS: Ho eliminato '{key}'.\n")
            else:
                print(f"\nJARVIS: Non trovo il fatto '{key}'.\n")
            continue

        if message.lower() == "/reset":
            conferma = input(
                "Attenzione: cancella tutta la cronologia. "
                "Scrivi SI per confermare: "
            ).strip()

            if conferma == "SI":
                jarvis.clear_history()
                print("\nJARVIS: Cronologia cancellata.\n")
            else:
                print("\nJARVIS: Operazione annullata.\n")
            continue

        try:
            answer = jarvis.chat(message)
            print(f"\nJARVIS: {answer}\n")
        except Exception as error:
            print(f"\nErrore durante la richiesta: {error}\n")


if __name__ == "__main__":
    main()
