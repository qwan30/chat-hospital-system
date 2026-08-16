// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import React from "react";
import { SsoCallback } from "./auth.sso.callback";

// Mock useNavigate from tanstack router
const mockNavigate = vi.fn();
vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual("@tanstack/react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children }: { children: React.ReactNode }) => children,
    useRouter: () => ({ state: { location: { pathname: "/" } } }),
  };
});

describe("auth.sso.callback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("handles valid SSO callback correctly", async () => {
    // Mock valid url
    Object.defineProperty(window, "location", {
      value: { href: "http://localhost/auth/sso/callback?code=abc&state=123" },
      writable: true,
    });
    const replaceStateSpy = vi.spyOn(window.history, "replaceState").mockImplementation(() => {});

    await act(async () => {
      render(React.createElement(SsoCallback));
    });

    // It should clear the URL
    expect(replaceStateSpy).toHaveBeenCalledWith({}, "", "http://localhost/auth/sso/callback");
    // It should start simulating steps
    expect(screen.getByText("Signing you in")).toBeTruthy();
  });

  it("fails closed on missing state or code", async () => {
    // Mock invalid url
    Object.defineProperty(window, "location", {
      value: { href: "http://localhost/auth/sso/callback?error=access_denied" },
      writable: true,
    });
    const replaceStateSpy = vi.spyOn(window.history, "replaceState").mockImplementation(() => {});

    await act(async () => {
      render(React.createElement(SsoCallback));
    });

    // It should clear the URL
    expect(replaceStateSpy).toHaveBeenCalledWith({}, "", "http://localhost/auth/sso/callback");

    // It should fail closed securely showing ErrorState
    expect(screen.getByText("SSO Sign In Failed")).toBeTruthy();
    expect(screen.getByText("Invalid SSO response from provider.")).toBeTruthy();
  });
});
