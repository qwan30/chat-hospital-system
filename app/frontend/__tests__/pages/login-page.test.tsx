import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import LoginPage from "@/app/login/page";

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ login: vi.fn(), apiUrl: null, token: null, isAuthenticated: false, isLoading: false }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("LoginPage", () => {
  it("renders heading", () => {
    render(<LoginPage />);
    expect(screen.getByText(/AI-Powered Hospital Knowledge Assistant/i)).toBeInTheDocument();
  });

  it("has SSO button", () => {
    render(<LoginPage />);
    expect(screen.getByText(/Sign in with Hospital SSO/i)).toBeInTheDocument();
  });

  it("renders feature bullets", () => {
    render(<LoginPage />);
    expect(screen.getByText(/HIPAA-compliant/i)).toBeInTheDocument();
  });
});
