import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export interface BoundingBox {
  id?: string;
  top: number;
  left: number;
  width: number;
  height: number;
  alignment_status: string;
}

export function GeometryOverlay({
  boxes,
  staleCount = 0,
}: {
  boxes: BoundingBox[];
  staleCount?: number;
}) {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {staleCount > 0 && (
        <div className="absolute top-2 left-2 right-2 pointer-events-auto">
          <Alert variant="destructive" className="bg-destructive/10 backdrop-blur">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {staleCount} {staleCount === 1 ? "annotation is" : "annotations are"} stale and cannot be exactly aligned.
            </AlertDescription>
          </Alert>
        </div>
      )}
      
      {boxes.map((box, i) => (
        <div
          key={box.id || i}
          className="absolute border-2 border-primary bg-primary/10 rounded-sm"
          style={{
            top: `${box.top * 100}%`,
            left: `${box.left * 100}%`,
            width: `${box.width * 100}%`,
            height: `${box.height * 100}%`,
          }}
        />
      ))}
    </div>
  );
}
