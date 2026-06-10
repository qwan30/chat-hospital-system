import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          "50": "var(--color-primary-50)",
          "100": "var(--color-primary-100)",
          "300": "var(--color-primary-300)",
          "500": "var(--color-primary-500)",
          "600": "var(--color-primary-600)",
          "700": "var(--color-primary-700)",
        },
        bg: {
          app: "var(--color-bg-app)",
          page: "var(--color-bg-page)",
          surface: "var(--color-bg-surface)",
          "surface-tint": "var(--color-bg-surface-tint)",
          sidebar: "var(--color-bg-sidebar)",
          overlay: "var(--color-bg-overlay)",
        },
        border: {
          subtle: "var(--color-border-subtle)",
          DEFAULT: "var(--color-border-default)",
          strong: "var(--color-border-strong)",
          focus: "var(--color-border-focus)",
        },
        text: {
          strong: "var(--color-text-strong)",
          DEFAULT: "var(--color-text-default)",
          muted: "var(--color-text-muted)",
          subtle: "var(--color-text-subtle)",
          inverse: "var(--color-text-inverse)",
          link: "var(--color-text-link)",
        },
        success: {
          "50": "var(--color-success-50)",
          "100": "var(--color-success-100)",
          "600": "var(--color-success-600)",
          "700": "var(--color-success-700)",
        },
        danger: {
          "100": "var(--color-danger-100)",
          "600": "var(--color-danger-600)",
          "700": "var(--color-danger-700)",
        },
        warning: {
          "100": "var(--color-warning-100)",
          "500": "var(--color-warning-500)",
          "700": "var(--color-warning-700)",
        },
        purple: {
          "100": "var(--color-purple-100)",
          "600": "var(--color-purple-600)",
        },
        cyan: {
          "100": "var(--color-cyan-100)",
          "600": "var(--color-cyan-600)",
        },
        chart: {
          blue: "var(--color-chart-blue)",
          green: "var(--color-chart-green)",
          orange: "var(--color-chart-orange)",
          purple: "var(--color-chart-purple)",
          grid: "var(--color-chart-grid)",
          axis: "var(--color-chart-axis)",
        },
      },
      borderRadius: {
        xs: "var(--radius-xs)",
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
        "3xl": "var(--radius-3xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        modal: "var(--shadow-modal)",
        popover: "var(--shadow-popover)",
      },
      zIndex: {
        sidebar: "10",
        topbar: "20",
        rail: "30",
        dropdown: "200",
        drawer: "250",
        backdrop: "500",
        modal: "600",
        toast: "700",
      },
      fontSize: {
        display: ["34px", { lineHeight: "42px", fontWeight: "700" }],
        h1: ["28px", { lineHeight: "36px", fontWeight: "700" }],
        h2: ["22px", { lineHeight: "30px", fontWeight: "700" }],
        h3: ["18px", { lineHeight: "26px", fontWeight: "700" }],
        h4: ["16px", { lineHeight: "24px", fontWeight: "700" }],
        metric: ["28px", { lineHeight: "34px", fontWeight: "700" }],
        "body-strong": ["14px", { lineHeight: "22px", fontWeight: "600" }],
        caption: ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "caption-strong": ["12px", { lineHeight: "16px", fontWeight: "600" }],
        micro: ["11px", { lineHeight: "14px", fontWeight: "500" }],
      },
    },
  },
};

export default config;
