"""Real Chrome test of the plugin on a real Koha (koha-testing-docker).

Run:
    venv/Scripts/python.exe plugins/koha/tests/test_browser.py install      the whole staff flow in the real UI
    venv/Scripts/python.exe plugins/koha/tests/test_browser.py chat         asks the chat one question
    venv/Scripts/python.exe plugins/koha/tests/test_browser.py load         only checks that the chat loads

Screenshots go to the folder in KOHA_SHOTS. Set it outside the project.
"""

import os
import re
import sys

from playwright.sync_api import sync_playwright

OPAC = os.environ.get("KOHA_OPAC", "http://127.0.0.1:8080")
STAFF = os.environ.get("KOHA_STAFF", "http://127.0.0.1:8081")
USER = os.environ.get("KOHA_USER", "koha")
PASSWORD = os.environ.get("KOHA_PASS", "koha")
SHOTS = os.environ.get("KOHA_SHOTS", ".")
WIDGET_ID = "asyntai_2bcd9dfbae24"
CLASS = "Koha::Plugin::Com::Asyntai::AIAssistant"
KPZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", "asyntai-koha.kpz")
TRIGGER = ".mccs-chat-trigger"


def shot(page, name):
    page.screenshot(path=os.path.join(SHOTS, name + ".png"), full_page=True)


def install(context):
    page = context.new_page()
    page.goto(STAFF + "/cgi-bin/koha/plugins/plugins-home.pl")
    page.fill("#userid", USER)
    page.fill("#password", PASSWORD)
    page.click("#submit-button")
    page.wait_for_selector("text=Upload plugin")

    page.goto(STAFF + "/cgi-bin/koha/plugins/plugins-upload.pl")
    page.set_input_files("#uploadfile", KPZ)
    page.click('form[enctype="multipart/form-data"] input[type="submit"], form[enctype="multipart/form-data"] button[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.goto(STAFF + "/cgi-bin/koha/plugins/plugins-home.pl")
    row = page.locator("tr", has_text="Asyntai AI Assistant").first
    shot(page, "staff_plugins_list")
    row.locator("button, a.dropdown-toggle").first.click()
    row.locator("a", has_text="Configure").click()
    page.wait_for_selector("#asyntai_plugin_configure")
    shot(page, "staff_settings_empty")

    page.fill("#widget_id", '<script async src="https://widget.asyntai.com/static/js/chat-widget.js" data-asyntai-id="%s"></script>' % WIDGET_ID)
    page.click("#asyntai_save")
    page.wait_for_selector("#asyntai_saved")
    assert page.input_value("#widget_id") == WIDGET_ID
    shot(page, "staff_settings_saved")
    print("ok   staff flow: upload, list, Configure, paste snippet, Save")

    page.wait_for_timeout(4000)
    assert page.locator(TRIGGER).count() == 0, "chat on the staff settings page"
    page.goto(STAFF + "/cgi-bin/koha/mainpage.pl")
    page.wait_for_timeout(4000)
    assert page.locator(TRIGGER).count() == 0, "chat on the staff main page"
    print("ok   no chat in the staff interface")
    page.close()


def load_opac(context, path="/"):
    page = context.new_page()
    messages = []
    page.on("console", lambda m: messages.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: messages.append("PAGEERROR " + str(e)))
    page.goto(OPAC + path, wait_until="load")
    try:
        page.wait_for_selector(TRIGGER, timeout=25000, state="visible")
        loaded = True
    except Exception:
        loaded = False
    return page, loaded, messages


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "load"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})

        if mode == "install":
            install(context)

        page, loaded, messages = load_opac(context)
        print("%s chat button on the OPAC home page" % ("ok  " if loaded else "FAIL"))
        policy = [m for m in messages if "Content Security Policy" in m or "Content-Security-Policy" in m]
        others = [m for m in messages if m not in policy]
        print("policy messages:", len(policy))
        for line in sorted(set(re.sub(r"'nonce-[^']+'", "'nonce'", m)[:230] for m in policy)):
            print("   ", line)
        print("other console messages:", len(others))
        for line in sorted(set(m[:230] for m in others)):
            print("   ", line)
        shot(page, "opac_home_%s" % mode)

        if loaded and mode != "chat":
            for path in ("/cgi-bin/koha/opac-search.pl?q=the", "/cgi-bin/koha/opac-detail.pl?biblionumber=1"):
                other, ok, _ = load_opac(context, path)
                print("%s chat button on %s" % ("ok  " if ok else "FAIL", path))
                shot(other, "opac_" + re.sub(r"\W+", "_", path)[-20:])
                other.close()

        if loaded and mode == "chat":
            page.click(TRIGGER)
            field = page.locator("#mccs-chat-form textarea, #mccs-chat-form input[type=text]").first
            field.wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(1500)
            shot(page, "opac_chat_open")
            field.fill("What can you help me with?")
            field.press("Enter")
            page.wait_for_timeout(25000)
            text = page.evaluate("() => { const h = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(Boolean); return h.map(r => r.textContent).join(' ') || document.body.innerText; }")
            shot(page, "opac_chat_answer")
            clean = re.sub(r"\s+", " ", re.sub(r"\.mccs[^{]*\{[^}]*\}|@[a-z-]+[^{]*\{[^}]*\}", " ", text))
            where = clean.rfind("What can you help me with?")
            print("reply text:", clean[where:where + 700])

        browser.close()


if __name__ == "__main__":
    main()
