import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import { AppRoutes } from "./routes";
import { queryClient } from "./query-client";
import { LanguageProvider } from "../lib/i18n";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

export function App() {
  return (
    <LanguageProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter future={routerFuture}>
          <AppRoutes />
        </BrowserRouter>
      </QueryClientProvider>
    </LanguageProvider>
  );
}
