
import io
import json
import unittest
from unittest.mock import patch

from flowlens.ai_assistant import ask_local_ai


class TestLocalAIAssistant(unittest.TestCase):
    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            ask_local_ai("   ", {"observations": 10})

    @patch("flowlens.ai_assistant.urlopen")
    def test_returns_model_answer(self, mock_urlopen):
        response_data = {
            "message": {
                "content": "The median gap is 93.8 hours."
            }
        }

        mock_response = io.BytesIO(
            json.dumps(response_data).encode("utf-8")
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        answer = ask_local_ai(
            "Explain the finding.",
            {"median_gap_hours": 93.8},
        )

        self.assertEqual(answer, "The median gap is 93.8 hours.")

    @patch("flowlens.ai_assistant.urlopen")
    def test_reports_unavailable_ollama(self, mock_urlopen):
        from urllib.error import URLError
        from flowlens.ai_assistant import LocalAIError

        mock_urlopen.side_effect = URLError("Connection refused")

        with self.assertRaises(LocalAIError):
            ask_local_ai("Explain the finding.", {"count": 10})


if __name__ == "__main__":
    unittest.main()
