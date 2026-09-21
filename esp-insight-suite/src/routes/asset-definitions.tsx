import { createFileRoute, redirect } from "@tanstack/react-router";

// Legacy URL compatibility: /asset-definitions/* moved into /engineering/*.
const MAP: Record<string, string> = {
  "": "/engineering",
  fleet: "/engineering/installations",
  catalog: "/engineering/catalog",
  well: "/engineering/installations/well",
  fluid: "/engineering/installations/fluid",
  assembly: "/engineering/installations/assembly",
  limits: "/engineering/installations/limits",
  validation: "/engineering/governance/validation",
  sources: "/engineering/governance/sources",
  quality: "/engineering/governance/quality",
  import: "/engineering/governance/import",
};

export const Route = createFileRoute("/asset-definitions")({
  beforeLoad: ({ location }) => {
    const rest = location.pathname.replace(/^\/asset-definitions\/?/, "");
    const [head, ...tail] = rest.split("/").filter(Boolean);
    const base = MAP[head ?? ""] ?? "/engineering";
    throw redirect({ href: [base, ...tail].join("/") });
  },
});
