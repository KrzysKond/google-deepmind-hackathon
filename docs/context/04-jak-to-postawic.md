# Jak to postawić

## Wymagania
- Python 3.10+
- konto i klucze Vapi

## Kroki
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `python3 -m pip install -e .`
3. Uzupełnij `.env` (`VAPI_API_KEY`, `VAPI_ASSISTANT_ID`, itd.)
4. Wygeneruj/uzupełnij markdowny:
   - `python3 -m onboarding_cli.cli generate-md`
5. Uruchom:
   - `python3 -m onboarding_cli.cli chat`
