# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from agent.history import history_manager

# Define the FastAPI app
app = FastAPI()

# CORS設定を追加（開発時にフロントエンドからアクセスできるように）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIのレスポンスモデル
class HistoryResponse(BaseModel):
    histories: List[Dict[str, Any]]
    total: int

class DeleteResponse(BaseModel):
    success: bool
    message: str


# API エンドポイント
@app.get("/api/history", response_model=HistoryResponse)
async def get_search_history(limit: int = 20, search: Optional[str] = None):
    """検索履歴を取得する"""
    try:
        if search:
            # 検索クエリが指定されている場合は検索
            histories = history_manager.search_histories(search)
        else:
            # 最近の履歴を取得
            histories = history_manager.get_recent_histories(limit)
        
        # データの妥当性をチェック
        valid_histories = []
        for history in histories:
            if isinstance(history, dict) and 'id' in history and 'query' in history:
                valid_histories.append(history)
        
        return HistoryResponse(histories=valid_histories, total=len(valid_histories))
    
    except Exception as e:
        # サイレントにエラーハンドリング - 履歴機能はオプショナルなので
        return HistoryResponse(histories=[], total=0)


@app.get("/api/history/{history_id}")
async def get_history_detail(history_id: str):
    """特定の履歴の詳細を取得する"""
    try:
        history = history_manager.get_history_by_id(history_id)
        if history is None:
            raise HTTPException(status_code=404, detail="履歴が見つかりません")
        return history
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="履歴の取得に失敗しました")


@app.delete("/api/history/{history_id}", response_model=DeleteResponse)
async def delete_search_history(history_id: str):
    """特定の検索履歴を削除する"""
    try:
        success = history_manager.delete_history(history_id)
        if success:
            return DeleteResponse(success=True, message="履歴を削除しました")
        else:
            return DeleteResponse(success=False, message="削除する履歴が見つかりません")
    
    except Exception:
        return DeleteResponse(success=False, message="履歴の削除に失敗しました")


@app.delete("/api/history", response_model=DeleteResponse)
async def clear_all_history():
    """すべての検索履歴を削除する"""
    try:
        success = history_manager.clear_all_history()
        if success:
            return DeleteResponse(success=True, message="すべての履歴を削除しました")
        else:
            return DeleteResponse(success=False, message="履歴の削除に失敗しました")
    
    except Exception:
        return DeleteResponse(success=False, message="履歴の削除に失敗しました")


@app.get("/api/health")
async def health_check():
    """ヘルスチェック用エンドポイント"""
    return {"status": "healthy", "message": "Search History API is running"}


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
