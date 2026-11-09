# Asyntai AI Assistant for Koha

[Asyntai](https://asyntai.com) adds an AI chat to your Koha public catalog (OPAC). It answers your patrons day and night, in more than 80 languages, from your own library content: opening hours, membership, loans, renewals, services and how to contact you.

## What the plugin does

- Adds the Asyntai chat to the pages of your public catalog, in every language and theme.
- Leaves the staff interface unchanged.
- Writes nothing to any page until you save a widget ID.
- Can show the chat to guests only, so patrons who are signed in do not see it.

The plugin makes no network request from your server. The browser of each OPAC visitor loads the chat script from `widget.asyntai.com`.

## Requirements

- Koha 24.11 or later. Tested on 24.11.21 and 26.05.05.
- Plugins enabled on your Koha server: `<enable_plugins>1</enable_plugins>` in `koha-conf.xml`. After you change this value, restart Koha.
- An Asyntai account. The free plan is enough to start.

## Installation

1. Sign in to Asyntai and open **Add to Your Website**. Copy your widget ID, for example `asyntai_ab12cd34`.
2. Download `asyntai-koha.kpz` from the [setup guide](https://asyntai.com/documentation/integrations/koha/) or from the releases of this repository.
3. In the Koha staff interface, open **Administration**, then **Manage plugins**, and upload the file.
4. Open the **Actions** menu of **Asyntai AI Assistant** and press **Configure**.
5. Paste the widget ID and press **Save**. The chat appears in your public catalog at once.

## Settings

| Setting | Meaning |
| --- | --- |
| Widget ID | The ID from your Asyntai dashboard. You can paste the whole snippet. An empty field switches the chat off. |
| Guests only | Patrons who are signed in to the catalog do not see the chat. |
| Widget script address | Change this only if Asyntai support asks you to. |

## Content security policy

Koha has no content security policy unless you switch it on. In `report-only` mode the chat works as usual. In `enabled` mode the default Koha policy blocks the chat, so set this value in `<opac><csp_header_value>` in `koha-conf.xml`, and then restart Koha:

```
default-src 'self'; script-src 'self' 'nonce-_CSP_NONCE_' https://widget.asyntai.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' https://asyntai.com https://widget.asyntai.com; object-src 'none'
```

The plugin adds the Koha nonce to its script tag.

## Development

```
prove -l t/
```

`t/settings.t` runs without Koha. `t/00-load.t` needs the Koha source in `PERL5LIB`.

`build_release.py` writes the `.kpz` file. `tests/test_koha.py` tests the plugin end to end on a real Koha. See [DEVELOPMENT.md](DEVELOPMENT.md).

## License

GPL-3.0. See [LICENSE](LICENSE).
