/**
 * ESP well index — the single spine that joins the three ESP data layers.
 *
 *  1. Operations demo layer      src/data/esp/fleet.ts + series.ts   (live-like OT values)
 *  2. Governed engineering layer Supabase esp_* tables via
 *                                src/lib/esp-catalog/queries.functions.ts
 *  3. Definition revision layer  src/data/esp/asset-definitions.ts   (versioned 16-section
 *                                definitions, provenance/confidence demo)
 *
 * Every screen should resolve a well through this module instead of keeping its
 * own copy of "which system / which model / how complete", so one number has one
 * source. Read-only: no writes, no control, no setpoints.
 */

import { fieldName, wells } from "./fleet";
import type { Well } from "./types";
import { latestDefinition, revisionsFor, summaryFor } from "./asset-definitions";
import type { EngineeringCatalog } from "@/lib/esp-catalog/queries.functions";
import { systemForWell, sectionsForSystem } from "@/lib/esp-catalog/selectors";

export type WellIndexEntry = {
  /** Canonical well id, e.g. "ESP-104". Same key in all three layers. */
  wellId: string;
  wellName: string;
  fieldId: string;
  fieldLabel: string;
  padName: string;
  /** Operations layer */
  operations: {
    state: Well["state"];
    healthIndex: number;
    runLifeDays: number;
    hz: number;
  };
  /** Definition revision layer */
  definition: {
    revisionCount: number;
    latestRevision: string | null;
    completenessPct: number;
    readiness: string;
  };
};

export function wellIndex(): WellIndexEntry[] {
  return wells.map((w) => {
    const summary = summaryFor(w);
    const latest = latestDefinition(w.id);
    return {
      wellId: w.id,
      wellName: w.name,
      fieldId: w.fieldId,
      fieldLabel: fieldName(w.fieldId),
      padName: w.padName,
      operations: {
        state: w.state,
        healthIndex: w.healthIndex,
        runLifeDays: w.runLifeDays,
        hz: w.hz,
      },
      definition: {
        revisionCount: revisionsFor(w.id).length,
        latestRevision: latest?.revision ?? null,
        completenessPct: summary.completenessPct,
        readiness: String(summary.readiness),
      },
    };
  });
}

export const wellIndexById = (wellId: string) => wellIndex().find((e) => e.wellId === wellId);

/**
 * Governed engineering resolution for a well, from the database catalog payload.
 * Kept separate from the deterministic layers above because it needs the loader
 * data supplied by the /engineering route tree.
 */
export function governedInstallation(catalog: EngineeringCatalog, wellId: string) {
  const system = systemForWell(catalog, wellId);
  if (!system) return null;
  return {
    systemId: system.id,
    assemblyType: system.assembly_type,
    matchStatus: system.match_status,
    matchConfidence: system.match_confidence,
    pumpModelId: system.normalized_pump_model_id,
    motorModelId: system.motor_model_id,
    cableModelId: system.cable_model_id,
    vsdModelId: system.vsd_model_id,
    sensorModelId: system.sensor_model_id,
    pumpSections: sectionsForSystem(catalog, system.id),
  };
}
