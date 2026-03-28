# Architektura

## Główne komponenty
- `onboarding_cli/cli.py` – wejście CLI (`ask`, `chat`, `generate-md`).
- `onboarding_cli/assistant.py` – orkiestracja: klasyfikacja pytania + odpowiedź.
- `onboarding_cli/markdown_context_client.py` – ładowanie kontekstu z plików `.md`.
- `onboarding_cli/vapi_client.py` – połączenie z Vapi API.
- `onboarding_cli/config.py` – konfiguracja ENV i walidacja.

## Przepływ
1. Użytkownik zadaje pytanie.
2. Kontekst ładowany jest z lokalnych plików Markdown.
3. Prompt z kontekstem trafia do Vapi.
4. CLI zwraca odpowiedź.
