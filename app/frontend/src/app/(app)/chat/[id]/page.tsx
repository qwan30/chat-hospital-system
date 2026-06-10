"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@/lib/auth-context";
import { sendChatMessage } from "@/lib/api-client";
import type { ChatThread, ChatMessage } from "@/lib/api-client";
import { UserBubble } from "@/components/chat/UserBubble";
import { AssistantCard } from "@/components/chat/AssistantCard";
import { Composer } from "@/components/chat/Composer";
import { StreamingAnswer } from "@/components/chat/StreamingAnswer";
import { SafeRefusalCard } from "@/components/chat/SafeRefusalCard";
import { HowItWorksRail } from "@/components/chat/HowItWorksRail";
import { GeneralKnowledgeToggle } from "@/components/chat/GeneralKnowledgeToggle";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, MessageSquare } from "lucide-react";
import Link from "next/link";

interface DisplayMessage { role: "user" | "assistant"; content: string; confidence?: string; isRefusal?: boolean; }

export default function ChatThreadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
    setMessages([
      { role: "user", content: "What are the key findings from the latest cardiac workup?" },
      { role: "assistant", content: "Based on the cardiac workup from May 12, 2025, key findings include mild left ventricular hypertrophy, preserved ejection fraction (EF 62%), and no significant valvular abnormalities.", confidence: "high" },
      { role: "user", content: "Any contraindications with current medications?" },
    ]);
  }, [id]);

  const handleSubmit = async (question: string) => {
    if (!apiUrl || !token) return;
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setStreaming(true);
    try {
      const response = await sendChatMessage({ apiUrl, token }, { question, thread_id: id });
      setMessages((prev) => [...prev, { role: "assistant", content: response.content, confidence: response.confidence }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "I cannot answer this question with sufficient confidence.", isRefusal: true }]);
    }
    setStreaming(false);
  };

  if (loading) return <div className="p-6 space-y-4"><Skeleton className="h-10 w-48" /><Skeleton className="h-[200px] w-full rounded-xl" /><Skeleton className="h-[100px] w-3/4 rounded-xl" /></div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/chat"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <h1 className="text-h1 text-text-strong">Cardiac Workup Discussion</h1>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {messages.map((msg, i) => msg.role === "user" ? <UserBubble key={i} message={msg.content} /> : msg.isRefusal ? <SafeRefusalCard key={i} reason="Insufficient clinical evidence available for this query." suggestions={["Try rephrasing your question", "Ensure relevant documents are indexed", "Consult a specialist"]} /> : <AssistantCard key={i} content={msg.content} confidence={(msg.confidence as "high" | "medium" | "low") || "high"} />)}
          {streaming && <StreamingAnswer />}
        </div>
        <div className="space-y-4">
          <HowItWorksRail />
          <GeneralKnowledgeToggle enabled={false} onToggle={() => {}} />
        </div>
      </div>
      <div className="max-w-3xl mx-auto"><Composer onSubmit={handleSubmit} disabled={streaming} /></div>
    </div>
  );
}
