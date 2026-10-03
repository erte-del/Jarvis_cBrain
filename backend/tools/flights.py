"""flights: search Google Flights in Chrome on this Mac. (read)

Google Flights has no API, so this works like amazon.py: Ultron opens a search in a
background tab, reads it and closes the tab. The search is Google's own plain-English
query URL (?q=Flights from Dubai to Istanbul on ...), so no form is filled in.

The layout is never parsed. Each result row's accessibility label already says the whole
flight in a sentence (price, airline, stops, airports, times), and Claude reads those. If
Google ever drops those labels, it falls back to the page's text, which Claude can still
read, so a redesign makes the answer messier but doesn't break it.

Ultron can't book: it returns the search link and the user picks a flight there and pays.
"""

import datetime as dt
from typing import Any
from urllib.parse import urlencode

from claude_agent_sdk import tool

from .homework import _run, _text

MAX_CHARS = 20_000
CABINS = ["economy", "premium economy", "business", "first"]

# The result rows' labels, or the page's text once 15 s have passed without any (no
# flights, or a new layout). '' means "not yet": _run asks again until the text settles.
READ = r"""(function () {
  if (document.readyState !== 'complete') return '';
  var seen = {}, rows = [];
  document.querySelectorAll('[aria-label]').forEach(function (e) {
    var t = e.getAttribute('aria-label');
    if (/^From .*flight/.test(t) && !seen[t]) { seen[t] = 1; rows.push(t.replace(/\s*Select flight\s*$/, '')); }
  });
  var text = document.body.innerText;
  if (!rows.length && performance.now() < 15000) return '';
  var insight = (text.match(/Prices are currently \w+[^\n]*/) || [''])[0];
  return document.title + '\n' + insight + '\n' + (rows.length ? rows.join('\n') : text);
})()"""


def search_url(args: dict[str, Any]) -> str:
    """The Google Flights search for these args. ValueError with a message for Claude."""
    origin, to = str(args.get("from") or "").strip(), str(args.get("to") or "").strip()
    if not origin or not to:
        raise ValueError("needs 'from' and 'to' (a city or airport code).")
    try:
        depart = dt.date.fromisoformat(str(args.get("depart") or ""))
        back = dt.date.fromisoformat(args["return"]) if args.get("return") else None
    except ValueError:
        raise ValueError("dates must be YYYY-MM-DD.") from None
    if depart < dt.date.today() or (back and back < depart):
        raise ValueError("the departure can't be in the past, or after the return.")
    adults, cabin = int(args.get("adults") or 1), str(args.get("cabin") or "economy").lower()
    if not 1 <= adults <= 9 or cabin not in CABINS:
        raise ValueError(f"adults must be 1 to 9 and cabin one of {', '.join(CABINS)}.")
    q = f"Flights from {origin} to {to} on {depart}"
    q += f" returning {back}" if back else " one way"
    q += f" for {adults} adults {cabin} class"
    return "https://www.google.com/travel/flights?" + urlencode({"q": q, "hl": "en"})


@tool(
    "flights",
    "Search Google Flights in Chrome on this Mac (read-only: a background tab, 10 to 20 "
    "seconds). from/to: a city or airport code. depart and return: YYYY-MM-DD (no return = "
    "one way). adults: default 1. cabin: economy (default), premium economy, business or "
    "first. Returns one line per flight (price for all passengers in the local currency, "
    "airline, stops and layovers, airports, times, duration), whether prices are low or high "
    "right now, and the search link. It can't book: the user picks a flight from the link "
    "and pays on the airline's or agent's site.",
    {
        "type": "object",
        "properties": {
            "from": {"type": "string"},
            "to": {"type": "string"},
            "depart": {"type": "string"},
            "return": {"type": "string"},
            "adults": {"type": "integer", "minimum": 1, "maximum": 9},
            "cabin": {"type": "string", "enum": CABINS},
        },
        "required": ["from", "to", "depart"],
    },
)
async def flights(args: dict[str, Any]) -> dict[str, Any]:
    try:
        url = search_url(args)
    except (ValueError, TypeError) as e:
        return _text(f"flights: {e}", True)
    try:
        _, text = await _run(url, READ, "tab", reuse=False)
    except (RuntimeError, OSError) as e:
        return _text(f"flights: {e}", True)
    if not text:
        return _text(f"flights: Google Flights opened but showed nothing. The search: {url}", True)
    return _text(f"{text[:MAX_CHARS]}\n\nSearch link (to pick a flight and book): {url}")
