"""Router tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import unittest

from brain.router import route


class RouterTest(unittest.TestCase):
    def check(self, text: str, model: str, **kwargs) -> None:
        self.assertEqual(route(text, **kwargs).model, model, f"{text!r}")

    def test_ui_override_wins(self):
        self.check("hi", "opus", override="opus")
        self.check("think hard about this", "haiku", override="haiku")

    def test_force_opus(self):
        for text in [
            "Use Opus: plan my week",
            "think hard about whether I should switch jobs",
            "Think really hard: what's wrong with this argument?",
            "can you think deeply about this",
            "do a deep dive on sourdough",
        ]:
            self.check(text, "opus")

    def test_force_haiku(self):
        for text in [
            "quick: capital of Peru?",
            "Quick question, how many ounces in a pound?",
            "use haiku to answer: 2+2",
            "quickly, what's 15% of 80",
        ]:
            self.check(text, "haiku")

    def test_force_sonnet(self):
        self.check("hi, use sonnet please", "sonnet")

    def test_small_talk(self):
        for text in ["hi", "Hey Jarvis!", "good morning", "thanks!", "Thank you so much",
                     "how are you?", "ok", "bye", "Got it."]:
            self.check(text, "haiku")

    def test_default_sonnet(self):
        for text in [
            "hi, can you help me write an email to my landlord?",
            "What's the difference between a Roth IRA and a traditional IRA?",
            "why?",
            "thanks, now summarise that in three bullets",
            "no, make it shorter",
        ]:
            self.check(text, "sonnet")

    def test_voice_short_goes_to_haiku(self):
        self.check("what time is it in Tokyo", "haiku", voice=True)
        self.check("what time is it in Tokyo", "sonnet", voice=False)
        self.check("explain in detail how a mortgage amortisation schedule works", "sonnet", voice=True)


if __name__ == "__main__":
    unittest.main()
