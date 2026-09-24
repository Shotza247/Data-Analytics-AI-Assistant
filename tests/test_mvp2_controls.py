from types import SimpleNamespace
import unittest

import openai
import pandas as pd
from streamlit.testing.v1 import AppTest


class FakeCompletions:
    last_messages = None

    def create(self, **kwargs):
        self.__class__.last_messages = kwargs["messages"]
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            "**Key Finding**\n\n"
                            "The Financial Services context and executive lending goal "
                            "were included in the analysis request."
                        )
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30),
        )


class FakeOpenAI:
    def __init__(self, api_key):
        self.chat = SimpleNamespace(completions=FakeCompletions())


class MVP2ControlsSmokeTest(unittest.TestCase):
    def test_business_context_reaches_provider_and_usage_is_recorded(self):
        original_openai = openai.OpenAI
        openai.OpenAI = FakeOpenAI
        try:
            app = AppTest.from_file("app.py", default_timeout=30)
            app.run()
            self.assertEqual(len(app.exception), 0)

            app.session_state["df"] = pd.read_csv("sample_data.csv")
            app.radio[0].set_value("Use my own key")
            app.selectbox(key="industry_select").set_value("Financial Services")
            app.text_area[0].set_value(
                "Explain revenue and customer-risk drivers for an executive lending team"
            )
            app.run()
            app.text_input[0].set_value("test-session-key")
            app.chat_input[0].set_value("Which region has the strongest performance?")
            app.run()

            self.assertEqual(len(app.exception), 0)
            system_prompt = FakeCompletions.last_messages[0]["content"]
            self.assertIn("Industry: Financial Services", system_prompt)
            self.assertIn("executive lending team", system_prompt)
            self.assertEqual(app.session_state["request_count"], 1)
            self.assertEqual(app.session_state["input_tokens_used"], 120)
            self.assertEqual(app.session_state["output_tokens_used"], 30)
            self.assertTrue(
                any("Financial Services context" in message.markdown[0].value for message in app.chat_message)
            )
        finally:
            openai.OpenAI = original_openai


if __name__ == "__main__":
    unittest.main()
