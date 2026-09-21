import { useState } from "react";
import { advisoriesFor } from "@/data/esp/advisor";
import type { Well } from "@/data/esp/types";
import { Panel, StatusPill } from "./ui";

export function AdvisorPanel({ well }: { well: Well }) {
  const [open, setOpen] = useState(true);
  const items = advisoriesFor(well);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="h-fit rounded-md border border-border bg-panel px-2 py-3 text-[11px] font-medium text-muted-foreground hover:text-foreground"
      >
        <span className="[writing-mode:vertical-rl]">ESP Advisor Preview</span>
      </button>
    );
  }

  return (
    <Panel
      title="ESP Advisor — preview"
      subtitle="Decision support only. No control actions are issued from this module."
      className="w-[330px] shrink-0"
      actions={
        <button type="button" onClick={() => setOpen(false)} className="text-[11px] text-muted-foreground hover:text-foreground">
          Collapse
        </button>
      }
      bodyClassName="p-2 space-y-2 max-h-[calc(100vh-190px)] overflow-y-auto panel-scroll"
      footer="Advisory content is illustrative and evidence-referenced; engineering review is required before any setpoint change."
    >
      {items.map((a) => (
        <article key={a.id} className="rounded border border-border bg-card p-2">
          <div className="flex items-center justify-between gap-2">
            <StatusPill tone={a.kind === "Predictive" ? "watch" : a.kind === "Optimization" ? "opportunity" : "info"}>
              {a.kind}
            </StatusPill>
            <span className="num text-[10px] text-muted-foreground">confidence {(a.confidence * 100).toFixed(0)}%</span>
          </div>
          <dl className="mt-2 space-y-1.5 text-[11px] leading-relaxed">
            <div>
              <dt className="text-[10px] tracking-wider text-muted-foreground uppercase">Observation</dt>
              <dd className="text-foreground">{a.observation}</dd>
            </div>
            <div>
              <dt className="text-[10px] tracking-wider text-muted-foreground uppercase">Engineering context</dt>
              <dd className="text-muted-foreground">{a.engineeringContext}</dd>
            </div>
            <div>
              <dt className="text-[10px] tracking-wider text-muted-foreground uppercase">Assessment</dt>
              <dd className="text-foreground">{a.assessment}</dd>
            </div>
            <div>
              <dt className="text-[10px] tracking-wider text-muted-foreground uppercase">Recommended checks / actions</dt>
              <dd>
                <ul className="ml-3 list-disc space-y-0.5 text-muted-foreground">
                  {a.actions.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </dd>
            </div>
            <div>
              <dt className="text-[10px] tracking-wider text-muted-foreground uppercase">Evidence references</dt>
              <dd className="flex flex-wrap gap-1 pt-0.5">
                {a.evidence.map((e) => (
                  <span key={e} className="rounded border border-border bg-panel px-1 py-0.5 text-[10px] text-muted-foreground">
                    {e}
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </article>
      ))}
    </Panel>
  );
}
