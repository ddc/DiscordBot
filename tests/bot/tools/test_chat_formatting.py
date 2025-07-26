"""Comprehensive tests for chat formatting utilities."""

from src.bot.tools import chat_formatting


class TestChatFormattingConstants:
    """Test Discord emoji constants."""

    def test_emoji_constants(self):
        """Test that all emoji constants are properly defined."""
        assert chat_formatting.NO_ENTRY == ":no_entry:"
        assert chat_formatting.WARNING_SIGN == ":warning:"
        assert chat_formatting.INFORMATION_SOURCE == ":grey_exclamation:"
        assert chat_formatting.QUESTION_MARK == ":question:"
        assert chat_formatting.SAD_FACE == ":frowning2:"
        assert chat_formatting.ROBOT == ":robot:"


class TestErrorFormatting:
    """Test error formatting functions."""

    def test_error_inline(self):
        """Test inline error formatting."""
        result = chat_formatting.error_inline("Test error")
        assert result == ":no_entry:\n`Test error`"

    def test_error_inline_empty_string(self):
        """Test inline error formatting with empty string."""
        result = chat_formatting.error_inline("")
        assert result == ":no_entry:\n``"

    def test_error_inline_special_characters(self):
        """Test inline error formatting with special characters."""
        result = chat_formatting.error_inline("Error with `backticks` and \n newlines")
        assert result == ":no_entry:\n`Error with `backticks` and \n newlines`"

    def test_error(self):
        """Test error formatting."""
        result = chat_formatting.error("Test error")
        assert result == ":no_entry:\nTest error"

    def test_error_empty_string(self):
        """Test error formatting with empty string."""
        result = chat_formatting.error("")
        assert result == ":no_entry:\n"

    def test_error_multiline(self):
        """Test error formatting with multiline text."""
        result = chat_formatting.error("Line 1\nLine 2")
        assert result == ":no_entry:\nLine 1\nLine 2"


class TestWarningFormatting:
    """Test warning formatting functions."""

    def test_warning_inline(self):
        """Test inline warning formatting."""
        result = chat_formatting.warning_inline("Test warning")
        assert result == ":warning:\n`Test warning`"

    def test_warning_inline_empty_string(self):
        """Test inline warning formatting with empty string."""
        result = chat_formatting.warning_inline("")
        assert result == ":warning:\n``"

    def test_warning(self):
        """Test warning formatting."""
        result = chat_formatting.warning("Test warning")
        assert result == ":warning:\nTest warning"

    def test_warning_empty_string(self):
        """Test warning formatting with empty string."""
        result = chat_formatting.warning("")
        assert result == ":warning:\n"


class TestInfoFormatting:
    """Test information formatting functions."""

    def test_info_inline(self):
        """Test inline info formatting."""
        result = chat_formatting.info_inline("Test info")
        assert result == ":grey_exclamation:\n`Test info`"

    def test_info_inline_empty_string(self):
        """Test inline info formatting with empty string."""
        result = chat_formatting.info_inline("")
        assert result == ":grey_exclamation:\n``"

    def test_info(self):
        """Test info formatting."""
        result = chat_formatting.info("Test info")
        assert result == ":grey_exclamation:\nTest info"

    def test_info_empty_string(self):
        """Test info formatting with empty string."""
        result = chat_formatting.info("")
        assert result == ":grey_exclamation:\n"


class TestQuestionFormatting:
    """Test question formatting functions."""

    def test_question_inline(self):
        """Test inline question formatting."""
        result = chat_formatting.question_inline("Test question")
        assert result == ":question:\n`Test question`"

    def test_question_inline_empty_string(self):
        """Test inline question formatting with empty string."""
        result = chat_formatting.question_inline("")
        assert result == ":question:\n``"

    def test_question(self):
        """Test question formatting."""
        result = chat_formatting.question("Test question")
        assert result == ":question:\nTest question"

    def test_question_empty_string(self):
        """Test question formatting with empty string."""
        result = chat_formatting.question("")
        assert result == ":question:\n"


class TestMarkdownFormatting:
    """Test Discord Markdown formatting functions."""

    def test_bold(self):
        """Test bold text formatting."""
        result = chat_formatting.bold("Test text")
        assert result == "**Test text**"

    def test_bold_empty_string(self):
        """Test bold formatting with empty string."""
        result = chat_formatting.bold("")
        assert result == "****"

    def test_bold_with_existing_markdown(self):
        """Test bold formatting with existing markdown."""
        result = chat_formatting.bold("*italic* text")
        assert result == "***italic* text**"

    def test_italics(self):
        """Test italic text formatting."""
        result = chat_formatting.italics("Test text")
        assert result == "*Test text*"

    def test_italics_empty_string(self):
        """Test italic formatting with empty string."""
        result = chat_formatting.italics("")
        assert result == "**"

    def test_strikethrough(self):
        """Test strikethrough text formatting."""
        result = chat_formatting.strikethrough("Test text")
        assert result == "~~Test text~~"

    def test_strikethrough_empty_string(self):
        """Test strikethrough formatting with empty string."""
        result = chat_formatting.strikethrough("")
        assert result == "~~~~"

    def test_underline(self):
        """Test underline text formatting."""
        result = chat_formatting.underline("Test text")
        assert result == "__Test text__"

    def test_underline_empty_string(self):
        """Test underline formatting with empty string."""
        result = chat_formatting.underline("")
        assert result == "____"


class TestCodeFormatting:
    """Test code formatting functions."""

    def test_box(self):
        """Test code block formatting."""
        result = chat_formatting.box("print('hello')")
        assert result == "```print('hello')```"

    def test_box_empty_string(self):
        """Test code block formatting with empty string."""
        result = chat_formatting.box("")
        assert result == "``````"

    def test_box_multiline(self):
        """Test code block formatting with multiline code."""
        code = "def test():\n    print('hello')"
        result = chat_formatting.box(code)
        assert result == "```def test():\n    print('hello')```"

    def test_inline(self):
        """Test inline code formatting."""
        result = chat_formatting.inline("variable")
        assert result == "`variable`"

    def test_inline_empty_string(self):
        """Test inline code formatting with empty string."""
        result = chat_formatting.inline("")
        assert result == "``"

    def test_inline_with_backticks(self):
        """Test inline code formatting with existing backticks."""
        result = chat_formatting.inline("code`with`backticks")
        assert result == "`code`with`backticks`"


class TestColoredTextFormatting:
    """Test colored text formatting functions."""

    def test_green_text(self):
        """Test green text formatting."""
        result = chat_formatting.green_text("Success message")
        assert result == "```css\nSuccess message\n```"

    def test_green_text_empty_string(self):
        """Test green text formatting with empty string."""
        result = chat_formatting.green_text("")
        assert result == "```css\n\n```"

    def test_green_text_multiline(self):
        """Test green text formatting with multiline text."""
        text = "Line 1\nLine 2"
        result = chat_formatting.green_text(text)
        assert result == "```css\nLine 1\nLine 2\n```"

    def test_red_text(self):
        """Test red text formatting."""
        result = chat_formatting.red_text("Error message")
        assert result == "```prolog\nError message\n```"

    def test_red_text_empty_string(self):
        """Test red text formatting with empty string."""
        result = chat_formatting.red_text("")
        assert result == "```prolog\n\n```"

    def test_orange_text(self):
        """Test orange text formatting."""
        result = chat_formatting.orange_text("Warning message")
        assert result == "```fix\nWarning message\n```"

    def test_orange_text_empty_string(self):
        """Test orange text formatting with empty string."""
        result = chat_formatting.orange_text("")
        assert result == "```fix\n\n```"


class TestFormattingCombinations:
    """Test combinations of formatting functions."""

    def test_bold_italic_combination(self):
        """Test combining bold and italic formatting."""
        text = "test"
        result = chat_formatting.bold(chat_formatting.italics(text))
        assert result == "***test***"

    def test_inline_with_colored_text(self):
        """Test inline code within colored text blocks."""
        inline_code = chat_formatting.inline("variable")
        result = chat_formatting.green_text(inline_code)
        assert result == "```css\n`variable`\n```"

    def test_error_with_formatted_text(self):
        """Test error formatting with pre-formatted text."""
        formatted_text = chat_formatting.bold("Important error")
        result = chat_formatting.error(formatted_text)
        assert result == ":no_entry:\n**Important error**"

    def test_nested_formatting(self):
        """Test nested formatting functions."""
        text = "important"
        result = chat_formatting.underline(chat_formatting.bold(chat_formatting.italics(text)))
        assert result == "__***important***__"


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_very_long_text(self):
        """Test formatting with very long text."""
        long_text = "A" * 1000
        result = chat_formatting.bold(long_text)
        assert result == f"**{long_text}**"
        assert len(result) == 1004  # original + 4 asterisks

    def test_text_with_unicode(self):
        """Test formatting with Unicode characters."""
        unicode_text = "Hello 🌍 世界"
        result = chat_formatting.italics(unicode_text)
        assert result == "*Hello 🌍 世界*"

    def test_text_with_discord_markdown_characters(self):
        """Test formatting with existing Discord markdown."""
        markdown_text = "*already* **bold** ~~striked~~ __underlined__"
        result = chat_formatting.box(markdown_text)
        assert result == "```*already* **bold** ~~striked~~ __underlined__```"

    def test_newlines_and_whitespace(self):
        """Test formatting with various whitespace characters."""
        whitespace_text = "  \n\t  Text with whitespace  \n\t  "
        result = chat_formatting.inline(whitespace_text)
        assert result == "`  \n\t  Text with whitespace  \n\t  `"
