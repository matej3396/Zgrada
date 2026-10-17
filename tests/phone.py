# Test « comme sur un vrai téléphone » : Pixel 7, tactile, processeur ralenti x4, réseau mobile, puis hors ligne.
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "www")
out = sys.argv[1] if len(sys.argv) > 1 else "."
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
res = []
def ok(c, m): res.append((bool(c), m)); print(("OK  " if c else "KO  ") + m)
try:
  with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**p.devices["Pixel 7"], locale="fr-CH", timezone_id="Europe/Zurich")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150, "downloadThroughput": 1.6e6 / 8, "uploadThroughput": 750e3 / 8})
    t = time.time(); pg.goto("http://localhost:8765/", wait_until="load"); pg.wait_for_selector("#app *")
    ok(time.time() - t < 4, "Premier affichage sur réseau 4G lent : %.1f s" % (time.time() - t))
    pg.screenshot(path=out + "/phone-1-intro.png")
    m = pg.evaluate("fetch('manifest.webmanifest').then(r=>r.json())")
    ok(m["display"] == "standalone" and any(i["sizes"] == "512x512" for i in m["icons"]), "Manifeste installable (icône, plein écran)")
    pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller || (location.reload(), false)", timeout=15000) if False else None
    pg.evaluate("navigator.serviceWorker.ready.then(()=>1)"); pg.reload(); pg.wait_for_selector("#app *")
    ok(pg.evaluate("!!navigator.serviceWorker.controller"), "Mode hors ligne prêt (service worker actif)")
    # Parcours au doigt : on touche les premiers boutons jusqu'à l'app
    taps = 0
    for _ in range(14):
      btn = pg.locator("#app button.btn:visible").first
      if btn.count() == 0: break
      t0 = time.time(); btn.tap(); pg.wait_for_timeout(50); taps += 1
      lat = time.time() - t0
      if lat > 0.4: ok(False, "Écran lent après un toucher : %.2f s" % lat)
      if pg.locator("nav.tabs, .tabbar, [data-act='tab']").count(): break
    ok(taps > 0, "Parcours d'accueil au doigt : %d touchers" % taps)
    pg.screenshot(path=out + "/phone-2-app.png")
    w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    ok(w[0] <= w[1], "Aucun débordement horizontal (%d ≤ %d px)" % tuple(w))
    small = pg.evaluate("""[...document.querySelectorAll('#app button,#app a,#app input')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.height<32&&getComputedStyle(e).visibility!=='hidden'}).length""")
    ok(small <= 3, "Zones tactiles trop petites (< 32 px) : %d" % small)
    # Hors ligne complet : avion
    ctx.set_offline(True); pg.reload(); pg.wait_for_selector("#app *", timeout=8000)
    ok(pg.locator("#app").inner_text().strip() != "", "Rouvre en mode avion, données gardées")
    pg.screenshot(path=out + "/phone-3-offline.png")
    ok(not errs, "Aucune erreur JavaScript" + ("" if not errs else " : " + errs[0][:120]))
    b.close()
finally:
  srv.terminate()
bad = [m for c, m in res if not c]
print("\n%d/%d OK" % (len(res) - len(bad), len(res))); sys.exit(1 if bad else 0)
