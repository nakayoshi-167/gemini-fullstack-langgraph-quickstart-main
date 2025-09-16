import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Loader2,
  Activity,
  Info,
  Search,
  TextSearch,
  Brain,
  Pen,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useEffect, useState } from "react";

export interface ProcessedEvent {
  title: string;
  data: any;
}

interface ActivityTimelineProps {
  processedEvents: ProcessedEvent[];
  isLoading: boolean;
}

export function ActivityTimeline({
  processedEvents,
  isLoading,
}: ActivityTimelineProps) {
  const [isTimelineCollapsed, setIsTimelineCollapsed] =
    useState<boolean>(false);
  const getEventIcon = (title: string, index: number) => {
    if (index === 0 && isLoading && processedEvents.length === 0) {
      return <Loader2 className="h-4 w-4 text-neutral-400 animate-spin" />;
    }
    
    const lowerTitle = title.toLowerCase();
    
    // Enhanced multi-agent system icons
    if (lowerTitle.includes("📋") || lowerTitle.includes("planning")) {
      return <span className="text-blue-400 text-sm">📋</span>;
    } else if (lowerTitle.includes("🔍") || lowerTitle.includes("parallel research")) {
      return <span className="text-green-400 text-sm">🔍</span>;
    } else if (lowerTitle.includes("📊") || lowerTitle.includes("aggregation")) {
      return <span className="text-yellow-400 text-sm">📊</span>;
    } else if (lowerTitle.includes("📝") || lowerTitle.includes("synthesis")) {
      return <span className="text-purple-400 text-sm">📝</span>;
    } else if (lowerTitle.includes("🔎") || lowerTitle.includes("quality review")) {
      return <span className="text-orange-400 text-sm">🔎</span>;
    } else if (lowerTitle.includes("✏️") || lowerTitle.includes("revision")) {
      return <span className="text-cyan-400 text-sm">✏️</span>;
    } else if (lowerTitle.includes("✨") || lowerTitle.includes("final polish")) {
      return <span className="text-emerald-400 text-sm">✨</span>;
    }
    
    // Legacy system icons
    else if (lowerTitle.includes("generating")) {
      return <TextSearch className="h-4 w-4 text-neutral-400" />;
    } else if (lowerTitle.includes("thinking")) {
      return <Loader2 className="h-4 w-4 text-neutral-400 animate-spin" />;
    } else if (lowerTitle.includes("reflection")) {
      return <Brain className="h-4 w-4 text-neutral-400" />;
    } else if (lowerTitle.includes("research")) {
      return <Search className="h-4 w-4 text-neutral-400" />;
    } else if (lowerTitle.includes("finalizing")) {
      return <Pen className="h-4 w-4 text-neutral-400" />;
    }
    
    return <Activity className="h-4 w-4 text-neutral-400" />;
  };

  const getEventStatus = (title: string, index: number) => {
    const isLastEvent = index === processedEvents.length - 1;
    const isCompleted = !isLoading || !isLastEvent;
    
    if (isCompleted) {
      return "bg-green-600 ring-green-600/30";
    } else {
      return "bg-blue-600 ring-blue-600/30 animate-pulse";
    }
  };

  useEffect(() => {
    if (!isLoading && processedEvents.length !== 0) {
      setIsTimelineCollapsed(true);
    }
  }, [isLoading, processedEvents]);

  return (
    <Card className="border-none rounded-lg bg-neutral-700 max-h-96">
      <CardHeader>
        <CardDescription className="flex items-center justify-between">
          <div
            className="flex items-center justify-start text-sm w-full cursor-pointer gap-2 text-neutral-100"
            onClick={() => setIsTimelineCollapsed(!isTimelineCollapsed)}
          >
            Research
            {isTimelineCollapsed ? (
              <ChevronDown className="h-4 w-4 mr-2" />
            ) : (
              <ChevronUp className="h-4 w-4 mr-2" />
            )}
          </div>
        </CardDescription>
      </CardHeader>
      {!isTimelineCollapsed && (
        <ScrollArea className="max-h-96 overflow-y-auto">
          <CardContent>
            {isLoading && processedEvents.length === 0 && (
              <div className="relative pl-8 pb-4">
                <div className="absolute left-3 top-3.5 h-full w-0.5 bg-neutral-800" />
                <div className="absolute left-0.5 top-2 h-5 w-5 rounded-full bg-neutral-800 flex items-center justify-center ring-4 ring-neutral-900">
                  <Loader2 className="h-3 w-3 text-neutral-400 animate-spin" />
                </div>
                <div>
                  <p className="text-sm text-neutral-300 font-medium">
                    Searching...
                  </p>
                </div>
              </div>
            )}
            {processedEvents.length > 0 ? (
              <div className="space-y-0">
                {processedEvents.map((eventItem, index) => {
                  const isLastEvent = index === processedEvents.length - 1;
                  const isCompleted = !isLoading || !isLastEvent;
                  
                  return (
                    <div key={index} className="relative pl-8 pb-4">
                      {index < processedEvents.length - 1 ||
                      (isLoading && index === processedEvents.length - 1) ? (
                        <div className={`absolute left-3 top-3.5 h-full w-0.5 ${isCompleted ? 'bg-green-600/50' : 'bg-neutral-600'}`} />
                      ) : null}
                      <div className={`absolute left-0.5 top-2 h-6 w-6 rounded-full flex items-center justify-center ring-4 ${getEventStatus(eventItem.title, index)} ring-neutral-700`}>
                        {getEventIcon(eventItem.title, index)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className={`text-sm font-medium ${isCompleted ? 'text-green-200' : 'text-blue-200'}`}>
                            {eventItem.title}
                          </p>
                          {isCompleted && (
                            <span className="px-1.5 py-0.5 bg-green-600/20 text-green-400 text-xs rounded-full">
                              ✓
                            </span>
                          )}
                          {!isCompleted && isLastEvent && isLoading && (
                            <span className="px-1.5 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded-full animate-pulse">
                              In Progress
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-neutral-300 leading-relaxed">
                          {typeof eventItem.data === "string"
                            ? eventItem.data
                            : Array.isArray(eventItem.data)
                            ? (eventItem.data as string[]).join(", ")
                            : JSON.stringify(eventItem.data)}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {isLoading && processedEvents.length > 0 && (
                  <div className="relative pl-8 pb-4">
                    <div className="absolute left-0.5 top-2 h-5 w-5 rounded-full bg-neutral-600 flex items-center justify-center ring-4 ring-neutral-700">
                      <Loader2 className="h-3 w-3 text-neutral-400 animate-spin" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-300 font-medium">
                        Searching...
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : !isLoading ? ( // Only show "No activity" if not loading and no events
              <div className="flex flex-col items-center justify-center h-full text-neutral-500 pt-10">
                <Info className="h-6 w-6 mb-3" />
                <p className="text-sm">No activity to display.</p>
                <p className="text-xs text-neutral-600 mt-1">
                  Timeline will update during processing.
                </p>
              </div>
            ) : null}
          </CardContent>
        </ScrollArea>
      )}
    </Card>
  );
}
