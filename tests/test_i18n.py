from t2_agent.i18n import t


def test_english_upload_prompt_and_summary_labels_are_available():
    assert "received the file" in t("English", "upload_received")
    assert t("English", "structured_summary") == "View structured summary"


def test_language_picker_is_bilingual_before_user_switches():
    assert t("中文", "language") == "界面语言 / Interface language"
    assert t("English", "language") == "界面语言 / Interface language"
    assert t("中文", "language_option_zh") == "中文 / Chinese"
    assert t("English", "language_option_en") == "English"
