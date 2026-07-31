import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface TypewriterTextProps {
  text: string;
  speed?: number; // Characters per tick
  delay?: number; // Delay before starting in ms
  className?: string;
  onComplete?: () => void;
  autoScroll?: boolean;
}

export function TypewriterText({
  text,
  speed = 5,
  delay = 0,
  className,
  onComplete,
  autoScroll = false,
}: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDisplayedText("");
    setIsComplete(false);

    if (!text) {
      setIsComplete(true);
      onComplete?.();
      return;
    }

    let currentLength = 0;
    let timeoutId: number;
    let frameId: number;

    const startTyping = () => {
      const tick = () => {
        currentLength += speed;
        if (currentLength >= text.length) {
          setDisplayedText(text);
          setIsComplete(true);
          onComplete?.();
          return;
        }

        setDisplayedText(text.slice(0, currentLength));
        frameId = requestAnimationFrame(tick);
      };

      frameId = requestAnimationFrame(tick);
    };

    if (delay > 0) {
      timeoutId = window.setTimeout(startTyping, delay);
    } else {
      startTyping();
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, [text, speed, delay, onComplete]);

  useEffect(() => {
    if (autoScroll && bottomRef.current && !isComplete) {
      bottomRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [displayedText, autoScroll, isComplete]);

  return (
    <div className={cn("relative whitespace-pre-wrap", className)}>
      {displayedText}
      {!isComplete && (
        <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-current animate-pulse" />
      )}
      {autoScroll && <div ref={bottomRef} />}
    </div>
  );
}
