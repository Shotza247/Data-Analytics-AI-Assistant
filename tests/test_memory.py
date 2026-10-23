import unittest

from memory import MAX_MEMORY_ENTRIES, build_session_memory


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


class SessionMemoryTest(unittest.TestCase):
    def test_empty_when_everything_is_inside_the_recent_window(self):
        self.assertEqual(build_session_memory(turns(4), 8), "")

    def test_summarises_only_turns_older_than_the_window(self):
        memory = build_session_memory(turns(6), 8)

        self.assertIn("Question number 0", memory)
        self.assertIn("Question number 1", memory)
        self.assertNotIn("Question number 2", memory)
        self.assertEqual(len(memory.splitlines()), 2)

    def test_uses_first_substantive_sentence_not_label_lines(self):
        memory = build_session_memory(turns(5), 8)

        self.assertIn("Found: Region 0 led revenue by a clear margin.", memory)
        self.assertNotIn("Key Finding", memory)
        self.assertNotIn("More detail follows", memory)

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
