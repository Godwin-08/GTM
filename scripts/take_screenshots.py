"""
Script de capture d'écran automatique pour le rapport LaTeX GTM.
Utilise Playwright (headless Chromium).
Exécuter APRÈS que le serveur Flask soit démarré sur http://127.0.0.1:5000
"""

import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "screens")
os.makedirs(OUT_DIR, exist_ok=True)

CREDS_ADMIN = {"email": "admin@galaxysolutions.ma", "password": "Admin@2026"}
CREDS_FORMATEUR = {"email": "karim.bensouda@galaxysolutions.ma", "password": "Karim@2026"}


def login(page, creds):
    page.goto(f"{BASE_URL}/")
    page.fill('input[name="email"]', creds["email"])
    page.fill('input[name="mot_de_passe"]', creds["password"])
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=8000)
    time.sleep(1)


def save(page, name, full_page=False):
    path = os.path.join(OUT_DIR, name)
    page.screenshot(path=path, full_page=full_page)
    print(f"  ✅  {name}")


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # ── 1. Page de connexion ──────────────────────────────────────
        print("\n[1/9] Login page")
        page.goto(f"{BASE_URL}/")
        time.sleep(1)
        save(page, "login_page.png")

        # ── 2. Dashboard Admin ────────────────────────────────────────
        print("[2/9] Dashboard Admin")
        login(page, CREDS_ADMIN)
        page.wait_for_selector("text=Sessions non annulées", timeout=8000)
        time.sleep(1.5)
        save(page, "dashboard_admin.png")

        # ── 3. Dashboard avec filtres ─────────────────────────────────
        print("[3/9] Dashboard filtres")
        # Sélectionner domaine Cybersécurité si disponible
        try:
            page.select_option('select[name="domaine_id"]', label="Cybersécurité")
            page.click('button:has-text("Appliquer")')
            time.sleep(1.5)
        except Exception:
            pass
        save(page, "dashboard_filtres.png")

        # ── 4. Liste des sessions ─────────────────────────────────────
        print("[4/9] Sessions list")
        page.goto(f"{BASE_URL}/sessions")
        time.sleep(1.5)
        save(page, "sessions_liste.png")

        # ── 5. Fiche détail session #1 ────────────────────────────────
        print("[5/9] Session detail")
        page.goto(f"{BASE_URL}/sessions/1")
        time.sleep(1.5)
        save(page, "session_detail.png")

        # ── 6. ACP ───────────────────────────────────────────────────
        print("[6/9] ACP")
        page.goto(f"{BASE_URL}/analytics/acp")
        time.sleep(2)
        save(page, "acp_nuage_clients.png")

        # ── 7. Notifications ─────────────────────────────────────────
        print("[7/9] Notifications")
        page.goto(f"{BASE_URL}/notifications")
        time.sleep(1.5)
        save(page, "notifications_page.png")

        # ── 8. Clients liste ─────────────────────────────────────────
        print("[8/9] Clients")
        page.goto(f"{BASE_URL}/clients")
        time.sleep(1.5)
        save(page, "clients_liste.png")

        # ── 9. Vue Formateur ──────────────────────────────────────────
        print("[9/9] Vue Formateur")
        # Déconnexion Admin
        page.goto(f"{BASE_URL}/")
        ctx2 = browser.new_context(viewport={"width": 1440, "height": 900})
        page2 = ctx2.new_page()
        login(page2, CREDS_FORMATEUR)
        page2.goto(f"{BASE_URL}/sessions")
        time.sleep(1.5)
        save(page2, "vue_formateur.png")
        ctx2.close()

        browser.close()

    print(f"\n✅ Toutes les captures sont dans : {OUT_DIR}")
    print("   Fichiers générés :")
    for f in sorted(os.listdir(OUT_DIR)):
        print(f"   - {f}")


if __name__ == "__main__":
    run()
