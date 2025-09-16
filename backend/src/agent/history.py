import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import uuid


@dataclass
class SearchHistory:
    """検索履歴のデータ構造"""
    id: str
    query: str
    timestamp: str
    effort: str
    model: str
    result: str
    search_queries: List[str]
    sources_count: int
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchHistory':
        return cls(**data)


class SearchHistoryManager:
    """検索履歴を管理するクラス"""
    
    def __init__(self, history_file: str = "search_history.json"):
        # より安全なパス処理
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.history_file = os.path.join(base_dir, history_file)
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """履歴ファイルが存在しない場合は作成"""
        try:
            # ディレクトリが存在しない場合は作成
            directory = os.path.dirname(self.history_file)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            if not os.path.exists(self.history_file):
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
        except Exception as e:
            # エラーが発生した場合は、デフォルトの場所に履歴ファイルを作成
            fallback_file = os.path.join(os.getcwd(), "search_history.json")
            self.history_file = fallback_file
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def save_history(
        self,
        query: str,
        effort: str,
        model: str,
        result: str,
        search_queries: List[str],
        sources_count: int = 0,
        duration_ms: Optional[int] = None
    ) -> str:
        """新しい検索履歴を保存"""
        history_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        new_history = SearchHistory(
            id=history_id,
            query=query,
            timestamp=timestamp,
            effort=effort,
            model=model,
            result=result,
            search_queries=search_queries,
            sources_count=sources_count,
            duration_ms=duration_ms
        )
        
        try:
            # 既存の履歴を読み込み
            histories = self.load_histories()
            
            # 新しい履歴を先頭に追加
            histories.insert(0, new_history.to_dict())
            
            # 最大100件まで保持
            histories = histories[:100]
            
            # ファイルに保存
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(histories, f, ensure_ascii=False, indent=2)
            
            return history_id
            
        except Exception as e:
            print(f"検索履歴の保存に失敗しました: {e}")
            return ""
    
    def load_histories(self) -> List[Dict[str, Any]]:
        """すべての検索履歴を読み込み"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # データ構造の検証
                if not isinstance(data, list):
                    return []
                return data
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            return []
        except Exception:
            return []
    
    def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """IDで特定の履歴を取得"""
        histories = self.load_histories()
        for history in histories:
            if history.get('id') == history_id:
                return history
        return None
    
    def delete_history(self, history_id: str) -> bool:
        """特定の履歴を削除"""
        try:
            histories = self.load_histories()
            original_length = len(histories)
            histories = [h for h in histories if h.get('id') != history_id]
            
            if len(histories) < original_length:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(histories, f, ensure_ascii=False, indent=2)
                return True
            return False
            
        except Exception as e:
            print(f"履歴の削除に失敗しました: {e}")
            return False
    
    def clear_all_history(self) -> bool:
        """すべての履歴を削除"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"履歴の全削除に失敗しました: {e}")
            return False
    
    def get_recent_histories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """最近の検索履歴を取得"""
        histories = self.load_histories()
        return histories[:limit]
    
    def search_histories(self, query: str) -> List[Dict[str, Any]]:
        """検索クエリで履歴を検索"""
        histories = self.load_histories()
        query_lower = query.lower()
        
        matched_histories = []
        for history in histories:
            if (query_lower in history.get('query', '').lower() or 
                query_lower in history.get('result', '').lower()):
                matched_histories.append(history)
        
        return matched_histories


# グローバルな履歴マネージャーインスタンス
history_manager = SearchHistoryManager()
