import asyncio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.context.resolver import resolve_context
from app.routing.capability_retrieval import retrieve_candidates
from app.contracts.routing import RouterInput
from app.routing.router import route_query_full
from app.workflow.runner import run_workflow

async def test_debug():
    msg = "What is the current operating status of FS-017?"
    frame = resolve_context("sess-debug", msg, well_id="FS-017")
    print(f"Context frame asset: id={frame.asset.id}, source={frame.asset.source}")
    
    cand_obj, cand_tools, cand_list = retrieve_candidates(msg)
    r_in = RouterInput(
        raw_message=msg,
        asset_id=frame.asset.id,
        asset_source=frame.asset.source,
        has_prior=bool(frame.session_snapshot.last_analysis_id),
        prior_objective=frame.session_snapshot.last_objective,
        turn_count=frame.session_snapshot.turn_count + 1,
        candidate_objectives=cand_obj,
        candidate_tools=cand_tools,
    )
    route_result = await route_query_full(r_in)
    decision = route_result.decision
    print(f"Route decision: route={decision.route}, intent={decision.intent}, objective_id={decision.objective_id}, args={decision.args}")
    
    result = await run_workflow(
        run_id="R-op01-test",
        session_id="sess-debug",
        objective_id=decision.objective_id,
        args=decision.args,
        confidence=decision.confidence,
    )
    print(f"Workflow result: ok={result.ok}, insufficient={result.insufficient_evidence}, missing={result.missing_required}")
    print(f"Result text: {result.text}")
    print(f"Call results count: {len(result.call_results)}")
    for i, cr in enumerate(result.call_results):
        print(f"  CR[{i}]: status={cr.status}, err={cr.error}, code={cr.error_code}")
        if cr.raw_response:
            print(f"    raw_keys: {list(cr.raw_response.keys()) if isinstance(cr.raw_response, dict) else type(cr.raw_response)}")

if __name__ == "__main__":
    asyncio.run(test_debug())
