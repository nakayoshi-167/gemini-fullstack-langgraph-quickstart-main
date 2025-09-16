import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Clock,
  Trash2,
  RefreshCw,
  ChevronLeft,
} from "lucide-react";
// DropdownMenuを使わずに、シンプルなボタンベースのメニューを使用

// 検索履歴のタイプ定義
interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: string;
  effort: string;
  model: string;
  result: string;
  search_queries: string[];
  sources_count: number;
  duration_ms?: number;
}

interface SearchHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectHistory: (historyItem: SearchHistoryItem) => void;
  apiUrl: string;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({
  isOpen,
  onClose,
  onSelectHistory,
  apiUrl,
}) => {
  const [histories, setHistories] = useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredHistories, setFilteredHistories] = useState<SearchHistoryItem[]>([]);

  // 履歴を読み込む
  const loadHistories = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/history?limit=50`);
      if (response.ok) {
        const data = await response.json();
        setHistories(data.histories);
      } else {
        console.error("履歴の取得に失敗しました");
      }
    } catch (error) {
      console.error("履歴の取得中にエラーが発生しました:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 履歴を削除する
  const deleteHistory = async (historyId: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/history/${historyId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setHistories(histories.filter(h => h.id !== historyId));
      } else {
        console.error("履歴の削除に失敗しました");
      }
    } catch (error) {
      console.error("履歴の削除中にエラーが発生しました:", error);
    }
  };

  // 全履歴を削除する
  const clearAllHistory = async () => {
    if (!confirm("すべての検索履歴を削除しますか？この操作は元に戻せません。")) {
      return;
    }
    
    try {
      const response = await fetch(`${apiUrl}/api/history`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setHistories([]);
      } else {
        console.error("履歴の削除に失敗しました");
      }
    } catch (error) {
      console.error("履歴の削除中にエラーが発生しました:", error);
    }
  };

  // 検索フィルタリング
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredHistories(histories);
    } else {
      const filtered = histories.filter(history =>
        history.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
        history.result.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredHistories(filtered);
    }
  }, [histories, searchTerm]);

  // コンポーネントマウント時に履歴を読み込み
  useEffect(() => {
    if (isOpen) {
      loadHistories();
    }
  }, [isOpen]);

  // 時刻をフォーマット
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays < 7) {
      return `${diffDays}日前`;
    } else {
      return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
    }
  };

  // モデル名の表示用フォーマット
  const formatModelName = (model: string) => {
    if (model.includes('2.5')) return '2.5 Pro';
    if (model.includes('2.0')) return '2.0 Flash';
    return model;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex">
      {/* サイドバー */}
      <div className="w-96 bg-neutral-900 h-full flex flex-col border-r border-neutral-700">
        {/* ヘッダー */}
        <div className="p-4 border-b border-neutral-700">
          <div className="flex items-center justify-between mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-neutral-400 hover:text-neutral-200"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              戻る
            </Button>
            <div className="flex gap-1">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={loadHistories}
                className="text-neutral-400 hover:text-neutral-200"
                title="履歴を更新"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={clearAllHistory}
                className="text-neutral-400 hover:text-red-400"
                title="すべての履歴を削除"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <h2 className="text-xl font-semibold text-neutral-100 mb-4">検索履歴</h2>

          {/* 検索バー */}
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-500" />
            <Input
              placeholder="履歴を検索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-neutral-800 border-neutral-600 text-neutral-100 placeholder-neutral-500"
            />
          </div>

          {/* 統計情報 */}
          <div className="flex items-center justify-between mt-4 text-sm text-neutral-400">
            <span>総検索数: {histories.length}</span>
            <span>7日以内: {histories.filter(h => {
              const diff = Date.now() - new Date(h.timestamp).getTime();
              return diff < 7 * 24 * 60 * 60 * 1000;
            }).length}</span>
          </div>
        </div>

        {/* 履歴リスト */}
        <ScrollArea className="flex-1">
          <div className="p-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-neutral-500" />
              </div>
            ) : filteredHistories.length === 0 ? (
              <div className="text-center py-8 text-neutral-500">
                {searchTerm ? "検索結果が見つかりません" : "検索履歴がありません"}
              </div>
            ) : (
              filteredHistories.map((history) => (
                <div
                  key={history.id}
                  className="group p-3 rounded-lg hover:bg-neutral-800 cursor-pointer transition-colors mb-2"
                  onClick={() => onSelectHistory(history)}
                >
                  {/* クエリと時刻 */}
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-medium text-neutral-100 line-clamp-2 flex-1">
                      {history.query}
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteHistory(history.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 h-6 w-6 text-neutral-500 hover:text-red-400 transition-opacity"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>

                  {/* 時刻と設定 */}
                  <div className="flex items-center text-xs text-neutral-500 mb-2">
                    <Clock className="h-3 w-3 mr-1" />
                    <span>{formatTimestamp(history.timestamp)}</span>
                  </div>

                  {/* メタデータバッジ */}
                  <div className="flex items-center gap-1 flex-wrap">
                    <Badge variant="outline" className="text-xs bg-neutral-700 text-neutral-300 border-neutral-600">
                      {formatModelName(history.model)}
                    </Badge>
                    <Badge variant="outline" className="text-xs bg-neutral-700 text-neutral-300 border-neutral-600">
                      {history.effort}
                    </Badge>
                    {history.sources_count > 0 && (
                      <Badge variant="outline" className="text-xs bg-neutral-700 text-neutral-300 border-neutral-600">
                        {history.sources_count} sources
                      </Badge>
                    )}
                  </div>

                  {/* 検索クエリプレビュー */}
                  {history.search_queries.length > 0 && (
                    <div className="mt-2 text-xs text-neutral-600">
                      {history.search_queries.slice(0, 2).join(", ")}
                      {history.search_queries.length > 2 && "..."}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* オーバーレイ（サイドバー外をクリックで閉じる） */}
      <div className="flex-1" onClick={onClose} />
    </div>
  );
};

export default SearchHistory;
