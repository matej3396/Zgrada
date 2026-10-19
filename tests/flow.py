# Parcours complet de la nouvelle Zgrada sur un Pixel 7 simulé.
import subprocess, sys, time, os
from playwright.sync_api import sync_playwright
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "www")
out = sys.argv[1] if len(sys.argv) > 1 else "."
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "-d", root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1); res = []; n = [0]
def ok(c, m): res.append((bool(c), m)); print(("OK  " if c else "KO  ") + m, flush=True)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(**p.devices["Pixel 7"], locale="fr-CH", timezone_id="Europe/Zurich")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept("Des cours de guitare"))
    def shot(name):
      n[0] += 1; pg.wait_for_timeout(250)
      w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
      ok(w[0] <= w[1], "%s : pas de débordement (%d/%d)" % (name, w[0], w[1]))
      pg.screenshot(path="%s/%02d-%s.png" % (out, n[0], name))
    def tap(sel, i=0): pg.locator(sel).nth(i).tap(); pg.wait_for_timeout(120)
    pg.goto("http://localhost:8766/"); pg.wait_for_selector("#app *")
    shot("accueil")
    fits = lambda: pg.evaluate("document.scrollingElement.scrollHeight <= innerHeight + 1")
    ok(fits(), "Accueil : tout tient sur un écran (%s)" % pg.evaluate("[document.scrollingElement.scrollHeight, innerHeight]"))
    for c in ["have|Mon appartement", "have|Un canapé", "have|Mes bras", "want|Un logement", "want|De l’aide pour porter", "want|Une camionnette"]:
      pg.locator('[data-arg="%s"]' % c).scroll_into_view_if_needed(); tap('[data-arg="%s"]' % c)
    pg.fill('[data-bind="me.name"]', "Matej"); pg.fill('[data-bind="me.from"]', "Clarens"); pg.fill('[data-bind="me.to"]', "Lausanne")
    pg.fill('[data-bind="me.date"]', time.strftime("%Y-%m-%d", time.localtime(time.time() + 50 * 864e2)))
    pg.fill('[data-bind="me.budget"]', "1700"); tap('[data-act="dog"]')
    ok(fits(), "Accueil rempli (avec le logement) : toujours sur un écran %s" % pg.evaluate("[document.scrollingElement.scrollHeight, innerHeight]"))
    pg.evaluate("""document.querySelectorAll('#app *').forEach(e=>{e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)*1.25)+'px'})""")
    ok(fits(), "Accueil avec texte agrandi x1,25 : sur un écran %s" % pg.evaluate("[document.scrollingElement.scrollHeight, innerHeight]"))
    shot("accueil-texte-agrandi"); pg.evaluate("render()")
    shot("demenagement-infos"); tap('[data-act="finish"]')
    ok(pg.locator(".tourcard").count() == 1, "Visite guidée lancée après l'accueil")
    for i in range(6):
      shot("visite-%d" % (i + 1)); tap('.tourcard [data-act="tourNext"]')
    ok(pg.locator(".tourcard").count() == 0, "Visite terminée")
    ok("Pour vous" in pg.inner_text("#app"), "Filtre « Pour vous » présent")
    # Zora
    tap('.asst'); shot("zora")
    for q, exp in [("je veux résilier mon bail", "Résilier son bail"), ("ma caution ?", "garantie de loyer"), ("trouver des gens pour porter le frigo", "Trouver des bras"), ("ou garer le camion", "place de parc"), ("xyzzy blabla", "pas trouvé")]:
      pg.fill("#askq", q); pg.locator("#askq").press("Enter"); pg.wait_for_timeout(150)
      ok(exp.lower() in pg.inner_text("#app").lower(), "Zora comprend : « %s »" % q)
    shot("zora-reponses"); tap('[data-act="back"]')
    # Texte agrandi (réglage d’accessibilité Android) : rien ne doit déborder des cartes
    pg.evaluate("""document.querySelectorAll('#app *').forEach(e=>{e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)*1.3)+'px'})""")
    bad = pg.evaluate("""[...document.querySelectorAll('.fcard')].filter(c=>{const r=c.getBoundingClientRect();return [...c.querySelectorAll('*')].some(e=>{const b=e.getBoundingClientRect();return b.width&&b.right>r.right+1})}).length""")
    ok(bad == 0, "Texte agrandi x1,3 : aucune carte ne déborde (%d)" % bad); shot("texte-agrandi"); pg.evaluate("render()")
    shot("explorer-pour-vous"); tap('[data-act="filter"][data-arg="tout"]'); shot("explorer-tout")
    tap('[data-act="open"][data-arg="d1"]'); ok("Ce qui colle" in pg.inner_text("#app"), "Logement : critères affichés"); shot("logement")
    tap('[data-act="fav"]'); tap('[data-act="compose"]'); shot("composer")
    ok(pg.locator('[data-act="send"]').is_enabled(), "Proposition préremplie (mon appartement)")
    tap('[data-act="send"]'); ok("Proposition envoyée" in pg.inner_text("#app"), "Conversation ouverte")
    pg.wait_for_selector('[data-act="accept"]', timeout=6000); shot("conversation")
    tap('[data-act="accept"]'); ok("deal" in pg.inner_text("#app"), "Écran « C’est un deal »"); shot("deal")
    tap('[data-act="thread"]'); tap('[data-act="done"]'); ok("Échange réalisé" in pg.inner_text("#app"), "Échange confirmé")
    pg.fill("#msg", "Merci encore !"); pg.locator("#msg").press("Enter"); pg.wait_for_timeout(1700); shot("conversation-fin")
    # Objet : message direct puis proposition
    tap('[data-act="tab"][data-arg="explorer"]') if pg.locator('[data-act="tab"]').count() else None
    pg.evaluate("S.stack=[];S.tab='explorer';render()")
    tap('[data-act="open"][data-arg="d2"]'); shot("objet"); tap('[data-act="compose"]'); tap('[data-act="giveText"]'); shot("composer-objet"); tap('[data-act="send"]')
    pg.wait_for_selector('[data-act="otherDay"]', timeout=6000); tap('[data-act="otherDay"]'); pg.wait_for_timeout(2000)
    ok(pg.locator('[data-act="accept"]').count() == 1, "Autre jour : nouvelle date proposée")
    # Publier
    pg.evaluate("S.stack=[];S.tab='explorer';render()"); tap('[data-act="publish"]'); tap('[data-act="pkind"][data-arg="aide"]')
    pg.fill('[data-bind="_pub.title"]', "Je prête ma voiture samedi"); tap('[data-act="pwants"][data-arg="Des cartons"]')
    pg.set_input_files("[data-photo]", os.path.join(root, "icon-512.png")); pg.wait_for_timeout(500); shot("publier")
    tap('[data-act="doPublish"]'); ok("Je prête ma voiture" in pg.inner_text("#app"), "Annonce publiée"); shot("mon-annonce")
    pg.evaluate("S.stack=[];render()"); tap('[data-act="tab"][data-arg="etapes"]'); tap('[data-act="task"][data-arg="bail"]'); shot("etapes")
    tap('[data-act="devis"][data-arg="nettoyage"]'); shot("devis")
    ok(pg.locator('[data-act="dsend"]').is_disabled(), "Devis : accord obligatoire avant l'envoi")
    tap('[data-act="dok"]'); tap('[data-act="dsend"]'); ok("Demande prête" in pg.inner_text("#app"), "Devis : demande prête, rien envoyé"); shot("devis-pret")
    pg.evaluate("S.stack=[];render()")
    tap('[data-act="tab"][data-arg="explorer"]'); tap('[data-act="filter"][data-arg="tout"]')
    ok("Sponsorisé" in pg.inner_text("#app"), "Explorer : emplacement « Sponsorisé » bien marqué"); shot("explorer-sponsor")
    tap('[data-act="tab"][data-arg="messages"]'); shot("messages")
    tap('[data-act="tab"][data-arg="moi"]'); shot("moi")
    # Réglages, données, développeur
    tap('[data-act="settings"]'); shot("reglages")
    pg.fill('[data-bind="me.email"]', "quelquun@exemple.ch"); pg.wait_for_timeout(300)
    ok(pg.locator('[data-act="dev"]').count() == 0, "Développeur caché pour une autre adresse")
    dev_mail = os.environ.get("DEV_MAIL")
    if dev_mail:
      pg.fill('[data-bind="me.email"]', dev_mail); pg.wait_for_timeout(400)
      ok(pg.locator('[data-act="dev"]').count() == 1, "Développeur visible avec l’adresse du propriétaire")
    else:
      pg.evaluate("S.dev=true;save();render()")
    with pg.expect_download() as dl: tap('[data-act="exportData"]')
    ok(dl.value.suggested_filename.startswith("zgrada-mes-donnees"), "Téléchargement des données : " + dl.value.suggested_filename)
    tap('[data-act="dev"]'); shot("developpeur")
    for a in ["msg", "offer", "rdv", "flake", "d7", "c10", "demoToggle", "raw"]:
      pg.evaluate("devAct('%s')" % a); pg.wait_for_timeout(60)
    ok(pg.evaluate("S.convs.some(c=>c.status==='flake')"), "Dev : faux bond simulé")
    ok(pg.evaluate("S.hideDemo===true"), "Dev : exemples masqués")
    pg.evaluate("devAct('crash')"); ok("Oups" in pg.inner_text("#app"), "Dev : écran d’erreur testé"); tap('[data-act="recover"]')
    pg.evaluate("devAct('demoToggle')")
    pg.evaluate("S.stack=[];S.tab='moi';render()"); tap('[data-act="credits"]')
    pg.fill("#ref", "abc123"); tap('[data-act="ref"]'); shot("credits")
    ok("Code d’un ami" in pg.inner_text("#app"), "Code ami accepté")
    # Persistance
    pg.reload(); pg.wait_for_selector("#app *"); ok("Vos crédits" in pg.inner_text("#app") or "crédits" in pg.inner_text("#app"), "Données gardées après rechargement")
    credits = pg.evaluate("S.credits"); ok(credits == 5 - 2 + 1 + 2 - 2 + 4 + 10 + 3, "Crédits cohérents : %s" % credits)
    # Retour Android
    pg.go_back(); pg.wait_for_timeout(200); ok(pg.evaluate("S.stack.length") == 0, "Bouton retour du téléphone")
    ok(not errs, "Aucune erreur JavaScript" + ("" if not errs else " : " + errs[0][:160]))
    b.close()
finally:
  srv.terminate()
bad = [m for c, m in res if not c]; print("\n%d/%d OK" % (len(res) - len(bad), len(res))); sys.exit(1 if bad else 0)
