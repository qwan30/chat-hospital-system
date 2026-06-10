interface UserBubbleProps {
  message: string;
  timestamp?: string;
}

export function UserBubble({ message, timestamp }: UserBubbleProps) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[70%]">
        <div className="bg-primary-600 text-white px-4 py-3 rounded-2xl rounded-br-md">
          <p className="text-[14px] leading-relaxed whitespace-pre-wrap">{message}</p>
        </div>
        {timestamp && <p className="text-[11px] text-text-subtle text-right mt-1 mr-1">{timestamp}</p>}
      </div>
    </div>
  );
}
