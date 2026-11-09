"""End to end test of the plugin against a real Koha (koha-testing-docker).

Run:
    venv/Scripts/python.exe plugins/koha/build_release.py
    venv/Scripts/python.exe plugins/koha/tests/test_koha.py

Uploads dist/asyntai-koha.kpz through the staff interface, saves settings through
the real form, reads real OPAC and staff pages, and uninstalls at the end. It
sends no chat message. See DEVELOPMENT.md for the rig.
"""

import os
import re
import sys

import requests

OPAC = os.environ.get("KOHA_OPAC", "http://127.0.0.1:8080")
STAFF = os.environ.get("KOHA_STAFF", "http://127.0.0.1:8081")
USER = os.environ.get("KOHA_USER", "koha")
PASSWORD = os.environ.get("KOHA_PASS", "koha")
WIDGET_ID = "asyntai_2bcd9dfbae24"
CLASS = "Koha::Plugin::Com::Asyntai::AIAssistant"
KPZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", "asyntai-koha.kpz")
TAG = re.compile(r"<script[^>]*data-asyntai-id=\"([^\"]+)\"[^>]*>", re.I)
DEFAULT_SRC = "https://widget.asyntai.com/static/js/chat-widget.js"
OPAC_PAGES = [
    "/",
    "/cgi-bin/koha/opac-main.pl",
    "/cgi-bin/koha/opac-search.pl?q=the",
    "/cgi-bin/koha/opac-detail.pl?biblionumber=1",
    "/cgi-bin/koha/opac-search.pl",
    "/cgi-bin/koha/opac-user.pl",
    "/cgi-bin/koha/opac-memberentry.pl",
    "/cgi-bin/koha/opac-topissues.pl",
    "/cgi-bin/koha/opac-shelves.pl?op=list&public=1",
    "/cgi-bin/koha/opac-does-not-exist.pl",
]

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("%s %s%s" % ("ok  " if ok else "FAIL", name, "" if ok else "  [%s]" % str(detail)[:300]))


def csrf(html):
    found = re.search(r'name="csrf_token"\s+value="([^"]+)"', html) or re.search(r'value="([^"]+)"\s+name="csrf_token"', html)
    return found.group(1) if found else ""


def login(base, path):
    session = requests.Session()
    page = session.get(base + path, timeout=120)
    data = {"csrf_token": csrf(page.text), "op": "cud-login", "login_op": "cud-login", "koha_login_context": "intranet" if base == STAFF else "opac", "login_userid": USER, "login_password": PASSWORD}
    answer = session.post(base + path, data=data, timeout=120)
    return session, answer


def tags(html):
    return TAG.findall(html)


def opac(path="/"):
    return requests.get(OPAC + path, timeout=120)


def configure_url():
    return "%s/cgi-bin/koha/plugins/run.pl?class=%s&method=configure" % (STAFF, CLASS)


def save(staff, **fields):
    page = staff.get(configure_url(), timeout=120)
    data = {"csrf_token": csrf(page.text), "class": CLASS, "method": "configure", "op": "cud-save", "widget_id": "", "script_url": ""}
    data.update(fields)
    return staff.post(STAFF + "/cgi-bin/koha/plugins/run.pl", data=data, timeout=120)


def uninstall(staff):
    staff.get("%s/cgi-bin/koha/plugins/plugins-uninstall.pl?class=%s" % (STAFF, CLASS), timeout=120)


def main():
    staff, answer = login(STAFF, "/cgi-bin/koha/mainpage.pl")
    check("staff login", "logout.x=1" in answer.text or "Log out" in answer.text, answer.status_code)
    version = re.search(r"Koha ([0-9.]+)", staff.get(STAFF + "/cgi-bin/koha/about.pl", timeout=120).text)
    print("Koha version:", version.group(1) if version else "unknown")

    uninstall(staff)
    before = opac()
    check("no tag before install", not tags(before.text))

    upload_page = staff.get(STAFF + "/cgi-bin/koha/plugins/plugins-upload.pl", timeout=120)
    with open(KPZ, "rb") as handle:
        uploaded = staff.post(
            STAFF + "/cgi-bin/koha/plugins/plugins-upload.pl",
            data={"csrf_token": csrf(upload_page.text), "op": "cud-Upload"},
            files={"uploadfile": ("asyntai-koha.kpz", handle, "application/octet-stream")},
            timeout=240,
        )
    check("upload answers", uploaded.status_code == 200, uploaded.status_code)

    home = staff.get(STAFF + "/cgi-bin/koha/plugins/plugins-home.pl", timeout=120).text
    check("plugin is listed", "Asyntai AI Assistant" in home)
    check("version is listed", "1.0.3" in home)
    check("configure link is listed", "method=configure" in home and CLASS in home)
    check("license data does not break the list", "Internal Server Error" not in home)

    check("no tag before a widget ID is saved", not tags(opac().text))

    page = staff.get(configure_url(), timeout=120)
    check("settings page opens", page.status_code == 200 and "asyntai_plugin_configure" in page.text, page.status_code)
    check("settings page has the fields", all(name in page.text for name in ('name="widget_id"', 'name="guests_only"', 'name="script_url"')))
    check("settings page has a CSRF token", csrf(page.text) != "")
    check("settings page has the Koha header", 'id="logged-in-info-full"' in page.text or "logout.x=1" in page.text)
    check("settings page has the guide link", "https://asyntai.com/documentation/integrations/koha/" in page.text)

    no_token = staff.post(STAFF + "/cgi-bin/koha/plugins/run.pl", data={"class": CLASS, "method": "configure", "op": "cud-save", "widget_id": WIDGET_ID}, timeout=120)
    check("save without a CSRF token is refused", no_token.status_code in (400, 403), no_token.status_code)
    check("nothing saved without a token", not tags(opac().text))

    anonymous = requests.post(STAFF + "/cgi-bin/koha/plugins/run.pl", data={"class": CLASS, "method": "configure", "op": "cud-save", "widget_id": WIDGET_ID}, timeout=120)
    check("save without login does not work", not tags(opac().text), anonymous.status_code)

    answer = save(staff, widget_id=WIDGET_ID)
    check("save shows the message", 'id="asyntai_saved"' in answer.text, answer.status_code)
    check("form keeps the saved ID", 'value="%s"' % WIDGET_ID in answer.text)

    for path in OPAC_PAGES:
        response = opac(path)
        found = tags(response.text)
        check("one tag on %s" % path, found == [WIDGET_ID], (response.status_code, found))

    html = opac().text
    check("tag has the default address", 'src="%s"' % DEFAULT_SRC in html)
    check("tag is async", re.search(r'<script async src="%s"' % re.escape(DEFAULT_SRC), html))
    check("tag sits inside the body", html.find("data-asyntai-id") > html.find("<body"))
    check("tag comes before the end of the body", html.find("data-asyntai-id") < html.rfind("</body>"))
    response = opac()
    policy = re.search(r"'nonce-([^']+)'", response.headers.get("Content-Security-Policy", "") or response.headers.get("Content-Security-Policy-Report-Only", ""))
    tag = re.search(r"<script[^>]*data-asyntai-id[^>]*>", response.text).group(0)
    if policy:
        check("tag has the nonce of the policy", 'nonce="%s"' % policy.group(1) in tag, tag)
    else:
        check("no nonce while the policy is off", 'nonce="' not in tag, tag)

    for name, path in (("main", "/cgi-bin/koha/mainpage.pl"), ("plugins", "/cgi-bin/koha/plugins/plugins-home.pl"), ("circulation", "/cgi-bin/koha/circ/circulation-home.pl"), ("catalog", "/cgi-bin/koha/catalogue/search.pl"), ("settings", "/cgi-bin/koha/plugins/run.pl?class=%s&method=configure" % CLASS)):
        check("no tag on staff %s page" % name, not tags(staff.get(STAFF + path, timeout=120).text))

    snippet = '<script async src="%s" data-asyntai-id="asyntai_abcdef123456"></script>' % DEFAULT_SRC
    answer = save(staff, widget_id=snippet)
    check("pasted snippet is saved", 'id="asyntai_saved"' in answer.text)
    check("form shows the ID from the snippet", 'value="asyntai_abcdef123456"' in answer.text)
    check("OPAC uses the ID from the snippet", tags(opac().text) == ["asyntai_abcdef123456"])

    for bad in ("hello", "asyntai_x", 'asyntai_abc123"><script>alert(1)</script>', "<script>alert(1)</script>"):
        answer = save(staff, widget_id=bad)
        check("bad ID shows the error: %s" % bad[:20], 'id="asyntai_error_widget_id"' in answer.text)
        check("bad ID is not stored: %s" % bad[:20], tags(opac().text) == ["asyntai_abcdef123456"])
        check("bad ID is escaped in the form: %s" % bad[:20], "<script>alert(1)" not in answer.text)

    for bad in ("http://example.org/w.js", "javascript:alert(1)", 'https://a.org/"><script>alert(2)</script>'):
        answer = save(staff, widget_id=WIDGET_ID, script_url=bad)
        check("bad address shows the error: %s" % bad[:20], 'id="asyntai_error_script_url"' in answer.text)
        check("bad address changes nothing: %s" % bad[:20], tags(opac().text) == ["asyntai_abcdef123456"])
        check("bad address is escaped in the form: %s" % bad[:20], "<script>alert(2)" not in answer.text)

    save(staff, widget_id=WIDGET_ID, script_url="https://cdn.example.org/w.js?a=1&b=2")
    check("own address is used and escaped", 'src="https://cdn.example.org/w.js?a=1&amp;b=2"' in opac().text)
    save(staff, widget_id=WIDGET_ID, script_url="   ")
    check("empty address goes back to the default", 'src="%s"' % DEFAULT_SRC in opac().text)

    patron, answer = login(OPAC, "/cgi-bin/koha/opac-user.pl")
    check("patron login", "logout.x=1" in answer.text or "opac-logout" in answer.text, answer.status_code)
    check("signed in patron sees the chat by default", tags(patron.get(OPAC + "/cgi-bin/koha/opac-user.pl", timeout=120).text) == [WIDGET_ID])

    answer = save(staff, widget_id=WIDGET_ID, guests_only="1")
    check("guests only box stays ticked", re.search(r'id="guests_only"[^>]*checked', answer.text))
    check("guest sees the chat with guests only", tags(opac().text) == [WIDGET_ID])
    check("signed in patron has no chat with guests only", not tags(patron.get(OPAC + "/cgi-bin/koha/opac-user.pl", timeout=120).text))
    check("signed in patron has no chat on search with guests only", not tags(patron.get(OPAC + "/cgi-bin/koha/opac-search.pl?q=the", timeout=120).text))
    reopened = staff.get(configure_url(), timeout=120).text
    check("guests only is kept after a reload", re.search(r'id="guests_only"[^>]*checked', reopened))

    answer = save(staff, widget_id=WIDGET_ID)
    check("guests only can be cleared", not re.search(r'id="guests_only"[^>]*checked', answer.text))
    check("signed in patron sees the chat again", tags(patron.get(OPAC + "/cgi-bin/koha/opac-user.pl", timeout=120).text) == [WIDGET_ID])

    answer = save(staff, widget_id="")
    check("empty ID is accepted", 'id="asyntai_saved"' in answer.text)
    check("empty ID switches the chat off", not tags(opac().text))

    save(staff, widget_id=WIDGET_ID)
    check("chat is back", tags(opac().text) == [WIDGET_ID])

    staff.get("%s/cgi-bin/koha/plugins/plugins-enable.pl?class=%s&method=disable" % (STAFF, CLASS), timeout=120)
    check("disable removes the chat", all(not tags(opac().text) for _ in range(4)))
    staff.get("%s/cgi-bin/koha/plugins/plugins-enable.pl?class=%s&method=enable" % (STAFF, CLASS), timeout=120)
    check("enable brings the chat back", all(tags(opac().text) == [WIDGET_ID] for _ in range(4)))
    check("settings stay after disable and enable", 'value="%s"' % WIDGET_ID in staff.get(configure_url(), timeout=120).text)

    uninstall(staff)
    check("uninstall removes the chat", all(not tags(opac().text) for _ in range(4)))
    check("uninstall removes the plugin from the list", "Asyntai AI Assistant" not in staff.get(STAFF + "/cgi-bin/koha/plugins/plugins-home.pl", timeout=120).text)

    print("\n%d checks, %d failed" % (len(results), results.count(False)))
    return 1 if False in results else 0


if __name__ == "__main__":
    sys.exit(main())
