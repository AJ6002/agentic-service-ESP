import { wellById, wells } from "./fleet";
import type { DesignCase, Well } from "./types";

function makeCase(w: Well, kind: DesignCase["kind"], idx: number): DesignCase {
  const isDesign = kind === "Design";
  const isWhatIf = kind === "What-if";
  const hz = isDesign ? w.designHz : isWhatIf ? +(w.hz + 1.5).toFixed(1) : w.hz;
  const speed = hz / Math.max(w.hz || w.designHz, 1);
  const liquid = isDesign ? w.designLiquidBpd : Math.round(w.liquidRateBpd * (isWhatIf ? speed : 1));
  const wcFrac = 1 - w.waterCutPct / 100;
  const tdh = Math.round(isDesign ? w.designTdhFt : w.designTdhFt * (isWhatIf ? 1.06 : 1.02));
  const pip = isDesign ? w.designPipPsi : isWhatIf ? Math.max(w.pipPsi - 55, 40) : w.pipPsi;
  const pdp = isDesign ? w.designPdpPsi : isWhatIf ? Math.round(w.pdpPsi * 1.05) : w.pdpPsi;
  const amps = isDesign ? w.designAmps : isWhatIf ? +(w.amps * Math.pow(speed, 3)).toFixed(1) : w.amps;
  return {
    id: `${w.id}-DC${idx}`,
    wellId: w.id,
    name: isDesign
      ? "Original install design"
      : isWhatIf
        ? `What-if: +1.5 Hz uplift`
        : "Current operating case",
    kind,
    author: isDesign ? "OEM sizing + AL Engineering" : isWhatIf ? "S. Devi (Artificial Lift)" : "ESP-PMM calculation engine",
    updated: isDesign ? w.installDate : "2026-08-13",
    status: isDesign ? "Superseded" : isWhatIf ? "Draft" : "Active",
    inputs: {
      reservoirPsi: w.reservoirPsi,
      piBpdPsi: w.piBpdPsi,
      waterCutPct: isDesign ? Math.max(w.waterCutPct - 9, 5) : w.waterCutPct,
      gorScfStb: w.gorScfStb,
      fluidSg: w.fluidSg,
      whpPsi: w.whpPsi,
      tubingId: 2.441,
      pumpSettingFt: 6200,
      perfDepthFt: 7400,
      hz,
      stages: w.stages,
    },
    outputs: {
      liquidBpd: liquid,
      oilBopd: Math.round(liquid * wcFrac),
      tdhFt: tdh,
      pipPsi: pip,
      pdpPsi: pdp,
      bhp: +((liquid * 0.0000616 * tdh * w.fluidSg) / 0.62).toFixed(1),
      efficiencyPct: isDesign ? 66.5 : isWhatIf ? 63.8 : +(60 + (w.healthIndex - 50) * 0.12).toFixed(1),
      motorLoadPct: Math.round((amps / w.motorRatingA) * 100),
      gvfPct: isDesign ? Math.max(w.gvfPct - 8, 1) : isWhatIf ? +(w.gvfPct + 2.5).toFixed(1) : w.gvfPct,
    },
    note: isDesign
      ? "Sizing basis at install: lower water cut and higher reservoir pressure than today."
      : isWhatIf
        ? "Simplified affinity-law scenario. Not an OEM-certified model — confirm inflow with a well test before execution."
        : "Calculated from current OTConnex signals and the active ESP model.",
  };
}

export const designCases: DesignCase[] = wells.flatMap((w) => [
  makeCase(w, "Design", 1),
  makeCase(w, "Current", 2),
  makeCase(w, "What-if", 3),
]);

export const casesForWell = (wellId: string) => designCases.filter((c) => c.wellId === wellId);

export const defaultCasePair = (wellId: string) => {
  const list = casesForWell(wellId);
  return { left: list[1] ?? list[0], right: list[2] ?? list[0] };
};

export const caseWell = (c: DesignCase) => wellById(c.wellId);
