# YourApp Flask Starter

Routes:
- `/` → Landing
- `/register` → Register
- `/login` → Login
- `/main` → Logged-in main
- `/account` → My Info

This uses an in-memory dict for users (demo only). Replace with a real DB (e.g., PostgreSQL or Supabase).

## Run
```bash
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install flask
python3 app.py
# open http://127.0.0.1:5000/
```
