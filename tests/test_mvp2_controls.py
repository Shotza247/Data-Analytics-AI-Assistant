from types import SimpleNamespace
import unittest

import openai
import pandas as pd
from streamlit.testing.v1 import AppTest


class FakeCompletions:
    last_messages = None
    cached_tokens = 0

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
            usage=SimpleNamespace(
                prompt_tokens=120,
                completion_tokens=30,
                prompt_tokens_details=SimpleNamespace(cached_tokens=self.cached_tokens),
            ),
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

    def _first_system_prompt(self, df, industry, goal):
        app = AppTest.from_file("app.py", default_timeout=30)
        app.run()
        app.session_state["df"] = df
        app.radio[0].set_value("Use my own key")
        app.selectbox(key="industry_select").set_value(industry)
        app.text_area[0].set_value(goal)
        app.run()
        app.text_input[0].set_value("test-session-key")
        app.chat_input[0].set_value("What is the average value?")
        app.run()
        self.assertEqual(len(app.exception), 0)
        return FakeCompletions.last_messages[0]["content"], app

    def test_only_recent_history_is_sent_to_the_provider(self):
        original_openai = openai.OpenAI
        openai.OpenAI = FakeOpenAI
        try:
            app = AppTest.from_file("app.py", default_timeout=30)
            app.run()
            app.session_state["df"] = pd.read_csv("sample_data.csv")
            app.session_state["messages"] = [
                {"role": "user" if i % 2 == 0 else "assistant", "content": f"earlier message {i}"}
                for i in range(20)
            ]
            app.radio[0].set_value("Use my own key")
            app.run()
            app.text_input[0].set_value("test-session-key")
            app.chat_input[0].set_value("latest question")
            app.run()

            self.assertEqual(len(app.exception), 0)
            sent = FakeCompletions.last_messages
            self.assertEqual(sent[0]["role"], "system")
            self.assertEqual(len(sent), 1 + 8)
            self.assertEqual(sent[-1]["content"], "latest question")
            self.assertNotIn("earlier message 0", "".join(m["content"] for m in sent[1:]))
            self.assertIn("# SESSION MEMORY", sent[0]["content"])
            self.assertIn("Asked: earlier message 0", sent[0]["content"])
            self.assertNotIn("earlier message 19", sent[0]["content"])
            self.assertEqual(len(app.session_state["messages"]), 22)
        finally:
            openai.OpenAI = original_openai

    def test_fixed_prompt_prefix_is_identical_across_datasets_and_contexts(self):
        original_openai = openai.OpenAI
        openai.OpenAI = FakeOpenAI
        FakeCompletions.cached_tokens = 64
        try:
            marker = "# SESSION CONTEXT"
            first, first_app = self._first_system_prompt(
                pd.read_csv("sample_data.csv"), "Retail / E-commerce", "Explain sales"
            )
            second, _ = self._first_system_prompt(
                pd.DataFrame({"alpha": [1, 2, 3], "beta": ["x", "y", "z"]}),
                "Healthcare",
                "Reduce readmissions",
            )

            self.assertIn(marker, first)
            self.assertEqual(first.split(marker)[0], second.split(marker)[0])
            self.assertNotEqual(first, second)
            self.assertEqual(first_app.session_state["cached_tokens_used"], 64)
        finally:
            FakeCompletions.cached_tokens = 0
            openai.OpenAI = original_openai


if __name__ == "__main__":
    unittest.main()
