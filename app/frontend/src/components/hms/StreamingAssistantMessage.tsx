import { useEffect } from "react";
import { useSearch } from "@tanstack/react-router";
import { ChatMessage, type ChatMessageData } from "./ChatMessage";
import { StreamingControls } from "./StreamingControls";
import { useStreamText } from "@/hooks/use-stream-text";

interface Props {
  /** Final message shape once streaming completes. */
  message: ChatMessageData;
  /** When true, autostart on mount. */
  autoStart?: boolean;
  /** Override failure simulation. */
  forceInterrupt?: boolean;
  onComplete?: () => void;
}

/**
 * Renders an assistant chat bubble whose `content` is streamed token-by-token.
 * Surfaces stop/retry/resume controls when the stream is interrupted or in flight.
 */
export function StreamingAssistantMessage({ message, autoStart = true, forceInterrupt, onComplete }: Props) {
  const search = useSearch({ strict: false }) as { simulate?: string };
  const shouldForce = forceInterrupt ?? search?.simulate === "stream-fail";

  const stream = useStreamText(message.content, {
    forceInterrupt: shouldForce,
    failureRate: shouldForce ? 1 : 0.06,
    onComplete: () => onComplete?.(),
  });

  useEffect(() => {
    if (autoStart) stream.start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const liveMsg: ChatMessageData = {
    ...message,
    content: stream.text + (stream.status === "streaming" ? "▍" : ""),
    // Only render citations once the stream is complete so [n] markers don't
    // dangle in mid-stream output.
    citations: stream.status === "complete" ? message.citations : undefined,
    extra: (
      <StreamingControls
        status={stream.status}
        error={stream.error}
        progress={stream.progress}
        total={message.content.length}
        onRetry={stream.retry}
        onResume={stream.resume}
        onStop={stream.stop}
      />
    ),
  };

  return <ChatMessage msg={liveMsg} />;
}