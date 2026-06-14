/**
 * Props for the {@link ChatLayout} component.
 *
 * Uses the slots pattern — each slot accepts any React node,
 * allowing the parent page to compose the chat interface from
 * independently loaded server/client components.
 */
interface ChatLayoutProps {
  /** The main chat thread area — message history + streaming answer. */
  thread: React.ReactNode;
  /** The right-side rail — patient context, how-it-works guide, suggestions. */
  rail: React.ReactNode;
  /** The bottom composer bar — input field + send button + file upload. */
  composer: React.ReactNode;
}

/**
 * ChatLayout — Two-Column Chat Interface Shell.
 *
 * Provides the canonical chat workspace layout used across the hospital AI
 * application. Uses CSS Grid to create a stable two-column layout:
 * a wide main thread area (min 680px) and a fixed-width right rail (420px).
 *
 * @remarks
 * - The composer is positioned `sticky` at the bottom of the thread column
 *   so it remains visible while scrolling through message history.
 * - Grid uses `minmax(680px, 1fr)` to prevent the thread column from
 *   collapsing below a readable width on smaller viewports.
 * - Designed as a slots-pattern layout — the parent page owns data fetching,
 *   this component only handles visual arrangement.
 *
 * @param props - Slotted child components for each region.
 * @returns The chat workspace grid layout.
 *
 * @example
 * ```tsx
 * <ChatLayout
 *   thread={<ChatThread messages={msgs} />}
 *   rail={<PatientContextRail patient={p} />}
 *   composer={<ChatComposer onSend={handleSend} />}
 * />
 * ```
 */
export function ChatLayout({ thread, rail, composer }: ChatLayoutProps) {
  return (
    <div className="grid min-h-[calc(100vh-var(--topbar-height)-48px)] grid-cols-[minmax(680px,1fr)_420px] gap-8">
      <section className="relative flex min-w-0 flex-col">
        {thread}
        <div className="sticky bottom-6 mt-auto">{composer}</div>
      </section>
      <aside className="space-y-4">{rail}</aside>
    </div>
  );
}
