import unittest

import de
import en

class TranslationsTest(unittest.TestCase):
    def test_de(self):
        for message in en.MESSAGES:
            self.assertIn(message, de.MESSAGES, '"%s" was not found in the translation de.py.' % (message, ))

if __name__ == '__main__':
    unittest.main()

