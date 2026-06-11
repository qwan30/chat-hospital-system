"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { createThread, sendChatMessage } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ContextChip } from "@/components/patient/ContextChip";
import { PromptGrid } from "@/components/chat/PromptGrid";
import { Composer } from "@/components/chat/Composer";
import { UserBubble } from "@/components/chat/UserBubble";
import { AssistantCard } from "@/components/chat/AssistantCard";
import { StreamingAnswer } from "@/components/chat/StreamingAnswer";
import { SafeRefusalCard } from "@/components/chat/SafeRefusalCard";
import { HowItWorksRail } from "@/components/chat/HowItWorksRail";
import { GeneralKnowledgeToggle } from "@/components/chat/GeneralKnowledgeToggle";
import { Button } from "@/components/ui/button";
import { ArrowLeft, MessageSquare } from "lucide-react";
import Link from "next/link";

interface Message { role: "user" | "assistant"; content: string; sections?: { title: string; content: string; citations?: number[] }[]; confidence?: "high" | "medium" | "low"; isRefusal?: boolean; }

export default function NewChatPage() {
  const { apiUrl, token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [gkEnabled, setGkEnabled] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);

  const handleSubmit = async (question: string) => {
    if (!apiUrl || !token) return;
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setStreaming(true);
    try {
      const tid = threadId || (await createThread({ apiUrl, token }, { title: question.slice(0, 80) })).id;
      if (!threadId) setThreadId(tid);
      const response = await sendChatMessage({ apiUrl, token }, { question, thread_id: tid });
      setMessages((prev) => [...prev, { role: "assistant", content: response.content, confidence: (response.confidence as "high" | "medium" | "low") || "high" }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "I cannot answer this question with sufficient confidence based on available evidence.", isRefusal: true }]);
    }
    setStreaming(false);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/chat"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <h1 className="text-h1 text-text-strong">New Conversation</h1>
      </div>

      {messages.length === 0 ? (
        <div className="max-w-3xl mx-auto space-y-6">
          <Card><CardContent className="py-8 text-center"><MessageSquare className="w-12 h-12 text-primary-300 mx-auto mb-3" /><h2 className="text-h3 text-text-strong mb-2">Start a Clinical Conversation</h2><p className="text-body text-text-muted max-w-md mx-auto">Ask a question about patient data, drug interactions, or clinical guidelines.</p></CardContent></Card>
          <GeneralKnowledgeToggle enabled={gkEnabled} onToggle={setGkEnabled} />
          <PromptGrid onSelect={(p) => handleSubmit(p.title)} />
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-4">
            {messages.map((msg, i) => msg.role === "user" ? <UserBubble key={i} message={msg.content} /> : msg.isRefusal ? <SafeRefusalCard key={i} reason="Insufficient clinical evidence available." suggestions={["Try a more specific query", "Check if relevant documents are indexed", "Consult a senior physician"]} /> : <AssistantCard key={i} content={msg.content} sections={msg.sections} confidence={msg.confidence} />)}
            {streaming && <StreamingAnswer />}
          </div>
          <div className="space-y-4">
            <HowItWorksRail />
            <GeneralKnowledgeToggle enabled={gkEnabled} onToggle={setGkEnabled} />
          </div>
        </div>
      )}
      <div className="max-w-3xl mx-auto"><Composer onSubmit={handleSubmit} disabled={streaming} /></div>
    </div>
  );
}
