import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/design-cases")({
  beforeLoad: () => {
    throw redirect({ to: "/engineering/design-cases" });
  },
});
