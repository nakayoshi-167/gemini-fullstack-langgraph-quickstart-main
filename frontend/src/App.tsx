import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { SearchHistory } from "@/components/SearchHistory";
import { Button } from "@/components/ui/button";
import { Clock, History } from "lucide-react";
import { useSearchHistory, SearchHistoryItem } from "@/hooks/useSearchHistory";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  
  // 検索履歴関連の状態
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  
  // APIのURL（環境によって切り替え）
  const apiUrl = import.meta.env.DEV
    ? "http://localhost:2024"
    : "http://localhost:8123";
  
  // 検索履歴のカスタムフック
  const searchHistoryHook = useSearchHistory(apiUrl);
  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
  }>({
    apiUrl: apiUrl,
    assistantId: "agent",
    messagesKey: "messages",
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      // Enhanced multi-agent system events
      if (event.enhanced_planner) {
        processedEvent = {
          title: "📋 Research Planning",
          data: `Created structured research plan with ${event.enhanced_planner.structured_plan?.sub_topics?.length || 0} sub-topics for comprehensive investigation.`,
        };
      } else if (event.focused_researcher) {
        const sources = event.focused_researcher.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 2).join(", ");
        processedEvent = {
          title: "🔍 Parallel Research",
          data: `Completed focused research - gathered ${numSources} sources${exampleLabels ? ` from ${exampleLabels}` : ''}.`,
        };
      } else if (event.aggregate_research_results) {
        processedEvent = {
          title: "📊 Research Aggregation",
          data: "Synchronizing all parallel research findings for comprehensive analysis.",
        };
      } else if (event.synthesizer) {
        processedEvent = {
          title: "📝 Report Synthesis",
          data: "Integrating research findings into coherent, structured report.",
        };
      } else if (event.revise_report) {
        processedEvent = {
          title: "✏️ Report Revision",
          data: "Improving report based on quality assessment feedback.",
        };
      } else if (event.critique_agent) {
        processedEvent = {
          title: "🔎 Quality Review",
          data: "Evaluating report quality and providing improvement feedback.",
        };
      } else if (event.final_polish) {
        processedEvent = {
          title: "✨ Final Polish",
          data: "Applying final touches and completing the research report.",
        };
        hasFinalizeEventOccurredRef.current = true;
        
        // Add a brief delay to ensure the completion is visible
        setTimeout(() => {
          console.log("✅ Multi-agent research completed successfully");
        }, 500);
      }
      // Academic Research Framework Events
      else if (event.academic_background_generator) {
        processedEvent = {
          title: "📚 Background & Objective",
          data: "Generating academic background and research objectives based on factual analysis.",
        };
      } else if (event.academic_framework_planner) {
        processedEvent = {
          title: "🏗️ Framework Planning",
          data: "Creating comprehensive academic paper framework with structured methodology.",
        };
      } else if (event.academic_abstract_generator) {
        processedEvent = {
          title: "📄 Abstract Generation",
          data: "Synthesizing key findings into concise academic abstract.",
        };
      } else if (event.literature_researcher) {
        processedEvent = {
          title: "🔍 Literature Research",
          data: "Conducting systematic literature review and fact verification from authoritative sources.",
        };
      } else if (event.academic_synthesizer) {
        processedEvent = {
          title: "📝 Academic Synthesis",
          data: "Integrating research findings into structured academic paper format.",
        };
      } else if (event.academic_reviewer) {
        processedEvent = {
          title: "🔍 Academic Review",
          data: "Performing rigorous academic quality review and fact-checking.",
        };
        hasFinalizeEventOccurredRef.current = true;
        
        // Add a brief delay to ensure the completion is visible
        setTimeout(() => {
          console.log("✅ Academic research completed successfully");
        }, 500);
      }
      // Legacy system events (for backward compatibility)
      else if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query?.search_query?.join(", ") || "",
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: "Analysing Web Research Results",
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      
      // Clear timeline and reset state for new search
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;
      
      // Add visual separator if there are existing messages
      if (thread.messages.length > 0) {
        // Small delay to ensure user can see the previous result
        setTimeout(() => {
          console.log("Starting new research session...");
        }, 100);
      }

      // convert effort to, initial_search_query_count and max_research_loops
      // low means max 1 loop and 1 query
      // medium means max 3 loops and 3 queries
      // high means max 10 loops and 5 queries
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      switch (effort) {
        case "low":
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: model,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  // 検索履歴からの再検索を処理
  const handleSelectHistory = useCallback((historyItem: SearchHistoryItem) => {
    // 履歴を閉じる
    setIsHistoryOpen(false);
    
    // 現在の状態をリセット
    setProcessedEventsTimeline([]);
    hasFinalizeEventOccurredRef.current = false;
    setError(null);

    // 履歴のパラメータを復元
    let initial_search_query_count = 3;
    let max_research_loops = 3;
    
    switch (historyItem.effort) {
      case "low":
        initial_search_query_count = 1;
        max_research_loops = 1;
        break;
      case "medium":
        initial_search_query_count = 3;
        max_research_loops = 3;
        break;
      case "high":
        initial_search_query_count = 5;
        max_research_loops = 10;
        break;
    }

    // 新しい検索を開始
    const newMessages: Message[] = [
      {
        type: "human",
        content: historyItem.query,
        id: Date.now().toString(),
      },
    ];

    thread.submit({
      messages: newMessages,
      initial_search_query_count: initial_search_query_count,
      max_research_loops: max_research_loops,
      reasoning_model: historyItem.model,
    });
  }, [thread]);

  // 検索履歴を開く
  const handleOpenHistory = useCallback(() => {
    setIsHistoryOpen(true);
  }, []);

  // 検索履歴を閉じる
  const handleCloseHistory = useCallback(() => {
    setIsHistoryOpen(false);
  }, []);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      {/* 検索履歴ボタン（固定位置） */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleOpenHistory}
        className="fixed top-4 left-4 z-40 bg-neutral-700/80 backdrop-blur-sm hover:bg-neutral-600 text-neutral-300 hover:text-neutral-100 border border-neutral-600"
      >
        <History className="h-4 w-4 mr-2" />
        履歴
      </Button>

      <main className="h-full w-full max-w-4xl mx-auto">
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
            />
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="flex flex-col items-center justify-center gap-4">
                <h1 className="text-2xl text-red-400 font-bold">Error</h1>
                <p className="text-red-400">{JSON.stringify(error)}</p>

                <Button
                  variant="destructive"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
      </main>

      {/* 検索履歴サイドバー */}
      <SearchHistory
        isOpen={isHistoryOpen}
        onClose={handleCloseHistory}
        onSelectHistory={handleSelectHistory}
        apiUrl={apiUrl}
      />
    </div>
  );
}
