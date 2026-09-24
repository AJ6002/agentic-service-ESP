import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/engineering/catalog")({
  component: () => <Outlet />,
});
