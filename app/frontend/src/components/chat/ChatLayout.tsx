interface ChatLayoutProps {
  thread: React.ReactNode;
  rail: React.ReactNode;
  composer: React.ReactNode;
}

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
