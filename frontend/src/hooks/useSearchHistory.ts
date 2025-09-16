import { useState, useCallback } from 'react';

// 検索履歴のタイプ定義
export interface SearchHistoryItem {
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

export const useSearchHistory = (apiUrl: string) => {
  const [histories, setHistories] = useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 履歴を取得する
  const fetchHistories = useCallback(async (limit: number = 50, search?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (search) {
        params.append('search', search);
      }
      
      const response = await fetch(`${apiUrl}/api/history?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`履歴の取得に失敗しました: ${response.status}`);
      }
      
      const data = await response.json();
      setHistories(data.histories);
      return data.histories;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の取得中にエラーが発生しました';
      setError(errorMessage);
      console.error('Search history fetch error:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl]);

  // 特定の履歴の詳細を取得する
  const fetchHistoryDetail = useCallback(async (historyId: string): Promise<SearchHistoryItem | null> => {
    try {
      const response = await fetch(`${apiUrl}/api/history/${historyId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('履歴が見つかりません');
        }
        throw new Error(`履歴の取得に失敗しました: ${response.status}`);
      }
      
      const history = await response.json();
      return history;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の詳細取得中にエラーが発生しました';
      setError(errorMessage);
      console.error('History detail fetch error:', err);
      return null;
    }
  }, [apiUrl]);

  // 履歴を削除する
  const deleteHistory = useCallback(async (historyId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${apiUrl}/api/history/${historyId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`履歴の削除に失敗しました: ${response.status}`);
      }
      
      // ローカルの状態からも削除
      setHistories(prev => prev.filter(h => h.id !== historyId));
      
      const data = await response.json();
      return data.success;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の削除中にエラーが発生しました';
      setError(errorMessage);
      console.error('History delete error:', err);
      return false;
    }
  }, [apiUrl]);

  // 全履歴を削除する
  const clearAllHistory = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${apiUrl}/api/history`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`履歴の削除に失敗しました: ${response.status}`);
      }
      
      // ローカルの状態もクリア
      setHistories([]);
      
      const data = await response.json();
      return data.success;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の削除中にエラーが発生しました';
      setError(errorMessage);
      console.error('History clear error:', err);
      return false;
    }
  }, [apiUrl]);

  // APIの健全性をチェック
  const checkApiHealth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${apiUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }, [apiUrl]);

  return {
    histories,
    isLoading,
    error,
    fetchHistories,
    fetchHistoryDetail,
    deleteHistory,
    clearAllHistory,
    checkApiHealth,
    // ヘルパー関数
    clearError: () => setError(null),
  };
};

export default useSearchHistory;
