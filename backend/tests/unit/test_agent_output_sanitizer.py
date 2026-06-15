from agent.output_sanitizer import sanitize_assistant_text_for_user_scripts


def test_sanitizer_removes_tamil_when_user_input_has_no_tamil():
    text = "Dear Care Corner, I would like to enquire about respite care. அ Thank you."

    sanitized = sanitize_assistant_text_for_user_scripts(text, "Help me draft an email in English.")

    assert "அ" not in sanitized
    assert "Dear Care Corner" in sanitized


def test_sanitizer_keeps_tamil_when_user_input_has_tamil():
    text = "Here is your Tamil phrase: நன்றி"

    sanitized = sanitize_assistant_text_for_user_scripts(text, "தமிழில் பதில் சொல்லுங்கள்")

    assert "நன்றி" in sanitized
