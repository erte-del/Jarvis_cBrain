"""Spotify helper tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import unittest

from tools.spotify import match_playlist, to_uri


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


if __name__ == "__main__":
    unittest.main()
