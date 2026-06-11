import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Star, MessageSquare } from "lucide-react";

export interface Testimonial {
  quote: string;
  author: string;
}

interface UserFeedbackCardProps {
  rating?: number;
  testimonials?: Testimonial[];
}

const DEFAULT_TESTIMONIALS: Testimonial[] = [
  { quote: "Saves me 30+ min per shift on chart review", author: "Dr. Miller" },
  { quote: "Citations give me confidence in AI answers", author: "Dr. Park" },
  { quote: "Medication review caught an interaction I missed", author: "Dr. Chen" },
];

export function UserFeedbackCard({ rating = 4.7, testimonials }: UserFeedbackCardProps) {
  const items = testimonials || DEFAULT_TESTIMONIALS;
  const wholeStars = Math.floor(rating);

  return (
    <Card><CardHeader><CardTitle className="text-h4 flex items-center gap-2"><MessageSquare className="w-4 h-4 text-text-subtle" />User Satisfaction</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2"><span className="text-metric text-text-strong">{rating}</span><span className="text-[13px] text-text-muted">/ 5.0</span><div className="flex gap-0.5 ml-2">{[1,2,3,4,5].map((s) => <Star key={s} className={"w-3.5 h-3.5 " + (s <= wholeStars ? "text-warning-500 fill-warning-500" : "text-text-subtle")} />)}</div></div>
        <div className="space-y-2">{items.map((item, i) => <div key={i} className="p-2.5 bg-bg-surface-tint rounded-lg"><p className="text-[13px] text-text-default italic">{item.quote}</p><p className="text-[11px] text-text-subtle mt-1">— {item.author}</p></div>)}</div>
      </CardContent>
    </Card>
  );
}
