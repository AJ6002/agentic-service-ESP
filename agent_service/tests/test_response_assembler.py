import json
import pytest
from app.contracts.events import ClarificationFrame, ErrorFrame
from app.synthesis.response_assembler import ResponseAssembler

@pytest.mark.anyio
async def test_assembler_clarification_stream():
    clarify = ClarificationFrame(
        run_id="R-cl-1",
        question="Which asset?",
        options=["FS-017", "FS-091"],
        slot="asset_id",
    )
    lines = []
    async for frame_line in ResponseAssembler.assemble_stream(
        run_id="R-cl-1",
        route="WORKFLOW",
        clarification=clarify,
    ):
        lines.append(json.loads(frame_line))

    assert len(lines) == 2
    assert lines[0]["type"] == "clarification"
    assert lines[0]["question"] == "Which asset?"
    assert lines[1]["type"] == "done"
    assert lines[1]["status"] == "PAUSED"

@pytest.mark.anyio
async def test_assembler_text_stream():
    lines = []
    async for frame_line in ResponseAssembler.assemble_stream(
        run_id="R-txt-1",
        route="SIMPLE",
        text="Total Dynamic Head (TDH) is the total equivalent height fluid is pumped.",
    ):
        lines.append(json.loads(frame_line))

    assert len(lines) == 2
    assert lines[0]["type"] == "text_delta"
    assert "TDH" in lines[0]["delta"]
    assert lines[1]["type"] == "done"
    assert lines[1]["status"] == "OK"

@pytest.mark.anyio
async def test_assembler_empty_text_guard():
    lines = []
    async for frame_line in ResponseAssembler.assemble_stream(
        run_id="R-err-1",
        route="SIMPLE",
        text="   ",
    ):
        lines.append(json.loads(frame_line))

    assert len(lines) == 2
    assert lines[0]["type"] == "error"
    assert lines[0]["code"] == "EMPTY_LLM_OUTPUT"
    assert lines[1]["type"] == "done"
    assert lines[1]["status"] == "ERROR"
