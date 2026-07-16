import { vi } from "vitest";

interface MockJsonResponse {
  body: unknown;
  status?: number;
  statusText?: string;
}

interface MockJsonRoute {
  path: string | RegExp;
  method?: string;
  response: MockJsonResponse;
}

function matchesRoute(
  url: string,
  method: string,
  route: MockJsonRoute,
): boolean {
  const routeMethod = (route.method ?? "GET").toUpperCase();
  const pathMatches =
    typeof route.path === "string"
      ? url === route.path
      : route.path.test(url);

  return pathMatches && method === routeMethod;
}

export function installJsonFetchMock(routes: MockJsonRoute[]) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const requestUrl =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const requestMethod = (
      init?.method ??
      (input instanceof Request ? input.method : "GET")
    ).toUpperCase();

    const matchedRoute = routes.find((route) =>
      matchesRoute(requestUrl, requestMethod, route),
    );

    if (!matchedRoute) {
      throw new Error(`Unexpected fetch request: ${requestMethod} ${requestUrl}`);
    }

    return new Response(JSON.stringify(matchedRoute.response.body), {
      status: matchedRoute.response.status ?? 200,
      statusText: matchedRoute.response.statusText ?? "OK",
      headers: {
        "Content-Type": "application/json",
      },
    });
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}
