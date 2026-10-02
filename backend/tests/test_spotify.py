"""Spotify helper tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import unittest
from unittest import mock

from tools import spotify
from tools.spotify import match_playlist, phone_of, play_body, to_uri


class ToUriTest(unittest.TestCase):
    def test_uris_and_links(self):
        self.assertEqual(to_uri("spotify:track:2JiDi0qAXsPwhPqA2qaKGt"), "spotify:track:2JiDi0qAXsPwhPqA2qaKGt")
        self.assertEqual(
            to_uri("https://open.spotify.com/intl-de/playlist/3k4dTiBvUW89wpnOkDcVRN?si=abc"),
            "spotify:playlist:3k4dTiBvUW89wpnOkDcVRN",
        )

    def test_rejects_anything_that_could_break_out_of_applescript(self):
        for bad in ['spotify:track:abc" & do shell script "rm -rf ~', "spotify:user:me", "Bohemian Rhapsody", ""]:
            self.assertIsNone(to_uri(bad), bad)


class MatchPlaylistTest(unittest.TestCase):
    def test_exact_before_partial(self):
        lists = [{"name": "Gym Mix 2"}, {"name": "gym mix"}, {"name": "Chill"}]
        self.assertEqual(match_playlist("Gym Mix", lists)["name"], "gym mix")
        self.assertEqual(match_playlist("chil", lists)["name"], "Chill")
        self.assertIsNone(match_playlist("jazz", lists))


class PhoneTest(unittest.TestCase):
    def test_picks_the_phone(self):
        mac = {"id": "m", "type": "Computer", "is_active": True}
        old, now = {"id": "a", "type": "Smartphone"}, {"id": "b", "type": "Smartphone", "is_active": True}
        self.assertEqual(phone_of([mac, old, now]), now)
        self.assertEqual(phone_of([mac, old]), old)
        self.assertIsNone(phone_of([mac]))

    def test_play_body(self):
        self.assertEqual(play_body("spotify:track:abc"), {"uris": ["spotify:track:abc"]})
        self.assertEqual(play_body("spotify:playlist:xyz"), {"context_uri": "spotify:playlist:xyz"})

    def test_plays_on_the_phone(self):
        calls = []
        devices = {"devices": [{"id": "p1", "name": "Pixel", "type": "Smartphone"}]}
        with mock.patch.object(spotify, "_get", return_value=devices), \
             mock.patch.object(spotify, "_call", side_effect=lambda *a, **k: calls.append((a, k)) or {}):
            self.assertEqual(spotify._phone("t", "play", "spotify:track:abc", {}), "Playing on Pixel.")
            self.assertEqual(spotify._phone("t", "next", None, {}), "Done: next on Pixel.")
        self.assertEqual(calls[0], (("t", "PUT", "/me/player/play", {"uris": ["spotify:track:abc"]}), {"device_id": "p1"}))
        self.assertEqual(calls[1], (("t", "POST", "/me/player/next"), {"device_id": "p1"}))
        with mock.patch.object(spotify, "_get", return_value={"devices": []}):
            self.assertEqual(spotify._phone("t", "pause", None, {}), "")


if __name__ == "__main__":
    unittest.main()
