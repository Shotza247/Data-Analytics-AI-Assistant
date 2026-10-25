import unittest

from memory import MAX_MEMORY_ENTRIES, build_memory_note, build_session_memory


def turns(count):
    messages = []
    for i in range(count):
        messages.append({"role": "user", "content": f"Question number {i} about revenue"})
        messages.append(
            {
                "role": "assistant",
                "content": f"**Key Finding**\n\nRegion {i} led revenue by a clear margin. More detail follows.",
            }
        )
    return messages


class MemoryNoteTest(unittest.TestCase):
    def test_prefers_sentence_with_a_number_over_background(self):
        note = build_memory_note(
            "Here is some background on how the orders are organised in the file. "
            "Electronics generated 38% of total revenue in the West region."
        )

        self.assertIn("Found: Electronics generated 38% of total revenue", note)
        self.assertNotIn("background", note)

    def test_adds_chart_title_from_metadata(self):
        metadata = ["Chart metadata: title='Electronics lead revenue', x_axis='Category', y_axis='Revenue'"]
        note = build_memory_note("Electronics lead with 38% of revenue overall.", metadata)

        self.assertIn("Chart: Electronics lead revenue", note)

    def test_ignores_charts_without_a_title(self):
        metadata = ["Chart metadata: title='', x_axis='Category', y_axis='Revenue'"]
        note = build_memory_note("Electronics lead with 38% of revenue overall.", metadata)

        self.assertNotIn("Chart:", note)

    def test_keeps_a_caveat_sentence(self):
        note = build_memory_note(
            "Fitness orders grew 12% between January and March. "
            "However, the sample is small and the trend may not hold."
        )

        self.assertIn("Caveat: However, the sample is small", note)

    def test_no_caveat_when_none_present(self):
        note = build_memory_note("Fitness orders grew 12% between January and March.")

        self.assertNotIn("Caveat:", note)

    def test_returns_empty_for_label_only_content(self):
        self.assertEqual(build_memory_note("**Key Finding**\n\nNone"), "")


class SessionMemoryTest(unittest.TestCase):
    def test_empty_when_everything_is_inside_the_recent_window(self):
        self.assertEqual(build_session_memory(turns(4), 8), "")

    def test_summarises_only_turns_older_than_the_window(self):
        memory = build_session_memory(turns(6), 8)

        self.assertIn("Question number 0", memory)
        self.assertIn("Question number 1", memory)
        self.assertNotIn("Question number 2", memory)
        self.assertEqual(len(memory.splitlines()), 2)

    def test_falls_back_to_content_when_no_stored_note(self):
        memory = build_session_memory(turns(5), 8)

        self.assertIn("Found: Region 0 led revenue by a clear margin.", memory)
        self.assertNotIn("Key Finding", memory)
        self.assertNotIn("More detail follows", memory)

    def test_uses_stored_note_when_present(self):
        messages = turns(5)
        messages[1]["memory_note"] = "Found: stored note | Chart: stored chart"
        memory = build_session_memory(messages, 8)

        self.assertIn("Asked: Question number 0 about revenue | Found: stored note | Chart: stored chart", memory)

    def test_skips_turns_with_an_empty_stored_note(self):
        messages = turns(6)
        messages[1]["content"] = "The PDF report is ready for your approval."
        messages[1]["memory_note"] = ""
        memory = build_session_memory(messages, 8)

        self.assertNotIn("PDF report", memory)
        self.assertNotIn("Question number 0", memory)
        self.assertIn("Question number 1", memory)

    def test_memory_is_capped_to_the_most_recent_entries(self):
        memory = build_session_memory(turns(30), 8)
        lines = memory.splitlines()

        self.assertEqual(len(lines), MAX_MEMORY_ENTRIES)
        self.assertIn("Question number 25", lines[-1])
        self.assertNotIn("Question number 0 ", memory)

    def test_long_text_is_truncated_and_markdown_is_removed(self):
        messages = [
            {"role": "user", "content": "x" * 500},
            {"role": "assistant", "content": "## **" + "word " * 200},
        ] + turns(4)
        memory = build_session_memory(messages, 8)
        first = memory.splitlines()[0]

        self.assertLess(len(first), 400)
        self.assertNotIn("**", first)
        self.assertNotIn("##", first)
        self.assertTrue(first.endswith("..."))

    def test_unanswered_user_message_is_skipped(self):
        messages = [{"role": "user", "content": "orphan question"}] + turns(5)
        memory = build_session_memory(messages, 8)

        self.assertNotIn("orphan question", memory)


if __name__ == "__main__":
    unittest.main()
