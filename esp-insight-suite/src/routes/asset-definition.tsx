import { createFileRoute, redirect } from "@tanstack/react-router";

// Legacy URL compatibility: /asset-definition/* is now /engineering/definition/*.
export const Route = createFileRoute("/asset-definition")({
  beforeLoad: ({ location }) => {
    const rest = location.pathname.replace(/^\/asset-definition\/?/, "");
    throw redirect({ href: rest ? `/engineering/definition/${rest}` : "/engineering/definition" });
  },
});
