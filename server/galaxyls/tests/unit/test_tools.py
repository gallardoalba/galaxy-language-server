import pytest
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.command import GalaxyToolCommandSnippetGenerator
from galaxyls.services.tools.generators.tests import GalaxyToolTestSnippetGenerator
from galaxyls.tests.unit.sample_data import TEST_TOOL_WITH_INPUTS_DOCUMENT
from galaxyls.tests.unit.utils import TestUtils
from pygls.types import Position, Range


class TestGalaxyToolXmlDocumentClass:
    def test_init_sets_properties(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        assert not tool.xml_document.is_empty

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool>", True),
            ("<tool></tool>", True),
        ],
    )
    def test_is_valid(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.is_valid == expected

    def test_find_tests_section_without_section_returns_none(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("notexistent")

        assert actual is None

    def test_find_tests_section_returns_expected(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("tests")

        assert actual
        assert actual.name == "tests"

    def test_get_element_content_range_of_unknown_element_returns_none(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element("unknown")

        actual = tool.get_element_content_range(node)

        assert actual is None

    @pytest.mark.parametrize(
        "source, element, expected",
        [
            ("<tool><tests/></tool>", "tests", None),
            ("<tool><tests></tests></tool>", "tests", Range(Position(0, 13), Position(0, 13))),
            ("<tool><tests>\n</tests></tool>", "tests", Range(Position(0, 13), Position(1, 0))),
            ("<tool>\n<tests>\n   \n</tests>\n</tool>", "tests", Range(Position(1, 7), Position(3, 0))),
            ("<tool>\n<tests>\n<test/></tests></tool>", "tests", Range(Position(1, 7), Position(2, 7))),
        ],
    )
    def test_get_element_content_range_of_element_returns_expected(self, source: str, element: str, expected: Range) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element(element)

        actual = tool.get_element_content_range(node)

        assert actual == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool></tool>", False),
            ("<tool><macros></macros></tool>", False),
            ("<tool><expand/></tool>", True),
            ("<tool><expand></tool>", True),
            ("<tool><expand></expand></tool>", True),
            ("<tool><expand/><expand/></tool>", True),
        ],
    )
    def test_uses_macros_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.uses_macros == expected

    def test_analyze_inputs_returns_expected_number_of_leaves(self) -> None:
        tool = GalaxyToolXmlDocument(TEST_TOOL_WITH_INPUTS_DOCUMENT)
        result = tool.analyze_inputs()

        assert len(result.leaves) == 3

    @pytest.mark.parametrize(
        "source, element_name, expected_position",
        [
            ("<tool></tool>", "tool", Position(0, 0)),
            ("<tool><description/><inputs></tool>", "description", Position(0, 6)),
            ("<tool><description/><inputs></tool>", "inputs", Position(0, 20)),
            ("<tool><macros><import></macros></tool>", "import", Position(0, 14)),
            ("<tool>\n<macros>\n<import></macros></tool>", "import", Position(2, 0)),
        ],
    )
    def test_get_position_before_element_returns_expected_position(
        self, source: str, element_name: str, expected_position: Position
    ) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        element = tool.find_element(element_name, maxlevel=4)

        assert element is not None
        actual_position = tool.get_position_before(element)
        assert actual_position == expected_position

    @pytest.mark.parametrize(
        "source, element_name, expected_position",
        [
            ("<tool></tool>", "tool", Position(0, 13)),
            ("<tool><description/><inputs></tool>", "description", Position(0, 20)),
            ("<tool><description/>\n<inputs></tool>", "description", Position(0, 20)),
            ("<tool>\n<description/>\n<inputs></tool>", "description", Position(1, 14)),
            ("<tool><description/><inputs></tool>", "inputs", Position(0, 28)),
            ("<tool><macros><import></macros></tool>", "import", Position(0, 22)),
            ("<tool>\n<macros>\n<import></macros></tool>", "import", Position(2, 8)),
        ],
    )
    def test_get_position_after_element_returns_expected_position(
        self, source: str, element_name: str, expected_position: Position
    ) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        element = tool.find_element(element_name, maxlevel=4)

        assert element is not None
        actual_position = tool.get_position_after(element)
        assert actual_position == expected_position


class TestGalaxyToolTestSnippetGeneratorClass:
    @pytest.mark.parametrize(
        "tool_file, expected_snippet_file",
        [
            ("simple_conditional_01.xml", "simple_conditional_01_test.xml"),
            ("simple_conditional_02.xml", "simple_conditional_02_test.xml"),
            ("simple_params_01.xml", "simple_params_01_test.xml"),
            ("simple_repeat_01.xml", "simple_repeat_01_test.xml"),
            ("simple_section_01.xml", "simple_section_01_test.xml"),
            ("simple_output_01.xml", "simple_output_01_test.xml"),
            ("simple_output_02.xml", "simple_output_02_test.xml"),
            ("complex_inputs_01.xml", "complex_inputs_01_test.xml"),
        ],
    )
    def test_build_snippet_returns_expected_result(self, tool_file: str, expected_snippet_file: str) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        expected_snippet = TestUtils.get_test_file_contents(expected_snippet_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        actual_snippet = generator._build_snippet()

        assert actual_snippet == expected_snippet

    @pytest.mark.parametrize(
        "source, expected_position",
        [
            ("<tool></tool>", Position(0, 6)),
            ("<tool><description/><inputs></tool>", Position(0, 28)),
            ("<tool><tests></tests></tool>", Position(0, 13)),
            ("<tool><tests/></tool>", Range(Position(0, 6), Position(0, 14))),
        ],
    )
    def test_find_snippet_position_returns_expected_result(self, source: str, expected_position: Position) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        actual_position = generator._find_snippet_insert_position()

        assert actual_position == expected_position


class TestGalaxyToolCommandSnippetGeneratorClass:
    @pytest.mark.parametrize(
        "tool_file, expected_snippet_file",
        [
            ("simple_conditional_01.xml", "simple_conditional_01_command.xml"),
            ("simple_conditional_02.xml", "simple_conditional_02_command.xml"),
            ("simple_params_01.xml", "simple_params_01_command.xml"),
            ("simple_repeat_01.xml", "simple_repeat_01_command.xml"),
            ("simple_section_01.xml", "simple_section_01_command.xml"),
            ("simple_output_01.xml", "simple_output_01_command.xml"),
            ("simple_output_02.xml", "simple_output_02_command.xml"),
            ("complex_inputs_01.xml", "complex_inputs_01_command.xml"),
        ],
    )
    def test_build_snippet_returns_expected_result(self, tool_file: str, expected_snippet_file: str) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        expected_snippet = TestUtils.get_test_file_contents(expected_snippet_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        actual_snippet = generator._build_snippet()

        assert actual_snippet == expected_snippet

    @pytest.mark.parametrize(
        "source, expected_position",
        [
            ("<tool></tool>", Position(0, 6)),
            ("<tool><description/><inputs></tool>", Position(0, 20)),
            ("<tool><command></command></tool>", Position(0, 15)),
            ("<tool><command/></tool>", Range(Position(0, 6), Position(0, 16))),
        ],
    )
    def test_find_snippet_position_returns_expected_result(self, source: str, expected_position: Position) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        actual_position = generator._find_snippet_insert_position()

        assert actual_position == expected_position
