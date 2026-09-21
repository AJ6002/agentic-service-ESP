import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/engineering/governance/")({
  beforeLoad: () => {
    throw redirect({ to: "/engineering/governance/validation" });
  },
});
