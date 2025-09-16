import os

from agent.tools_and_schemas import (
    SearchQueryList, 
    Reflection, 
    ResearchPlan, 
    StructuredResearchPlan, 
    SubTopicResearch, 
    CitedAnswer, 
    CritiqueAssessment,
    # Academic Research Framework Schemas
    AcademicBackground,
    AcademicFramework,
    AcademicAbstract,
    LiteratureResearch,
    AcademicReview
)
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    ResearchPlanState,
    WebSearchState,
    PlannerState,
    ParallelResearchState,
    SynthesisState,
    CritiqueState,
    # Academic Research Framework State Classes
    AcademicBackgroundState,
    AcademicFrameworkState,
    AcademicAbstractState,
    LiteratureResearchState,
    AcademicReviewState,
)
from agent.configuration import Configuration
from agent.prompts import (
    get_current_date,
    research_plan_instructions,
    query_writer_instructions,
    web_searcher_instructions,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    SYNTHESIZER_PROMPT,
    CRITIQUE_PROMPT,
    # Academic Research Framework Prompts
    ACADEMIC_BACKGROUND_PROMPT,
    ACADEMIC_FRAMEWORK_PROMPT,
    ABSTRACT_GENERATOR_PROMPT,
    LITERATURE_RESEARCH_PROMPT,
    ACADEMIC_REPORT_SYNTHESIS_PROMPT,
    ACADEMIC_REVIEW_PROMPT
)
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls
)
from agent.history import history_manager
import time

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# Enhanced Multi-Agent Nodes for Deep Research Architecture

def enhanced_planner(state: OverallState, config: RunnableConfig) -> PlannerState:
    """Enhanced planner that creates structured research plan with sub-topics.
    
    Creates a hierarchical research plan with multiple sub-topics that can be executed 
    by parallel researcher agents. This approach enables comprehensive coverage of 
    complex topics through focused, parallel investigation of different aspects.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Initialize Gemini 2.5 Pro for enhanced planning
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0.3,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(StructuredResearchPlan)
    
    # Format the enhanced planner prompt
    user_question = get_research_topic(state["messages"])
    formatted_prompt = PLANNER_PROMPT.format(user_question=user_question)
    
    # Generate the structured research plan
    result = structured_llm.invoke(formatted_prompt)
    
    # Convert to state format
    sub_topics_list = []
    for sub_topic in result.sub_topics:
        sub_topics_list.append({
            "topic_name": sub_topic.topic_name,
            "search_queries": sub_topic.search_queries
        })
    
    return {
        "structured_plan": {
            "research_question": result.research_question,
            "sub_topics": sub_topics_list,
            "estimated_depth": result.estimated_depth
        },
        "current_phase": "planning",
        "start_time": time.time(),
        "original_query": user_question,
        "effort_level": "comprehensive",  # Enhanced planning implies comprehensive research
        "revision_count": 0
    }


def run_parallel_research(state: OverallState, config: RunnableConfig):
    """Dispatcher node that launches parallel researcher agents.
    
    Distributes research sub-topics to multiple specialized researcher agents that can 
    work in parallel. Uses LangGraph's Send directive to spawn multiple parallel research branches,
    enabling efficient and comprehensive information gathering across different aspects of the topic.
    """
    structured_plan = state.get("structured_plan", {})
    sub_topics = structured_plan.get("sub_topics", [])
    
    # Create parallel Send directives for each sub-topic
    parallel_sends = []
    for idx, sub_topic in enumerate(sub_topics):
        parallel_sends.append(
            Send(
                "focused_researcher",
                {
                    "topic_name": sub_topic["topic_name"],
                    "search_queries": sub_topic["search_queries"],
                    "sub_topic_id": str(idx)
                }
            )
        )
    
    return parallel_sends


def focused_researcher(state: ParallelResearchState, config: RunnableConfig) -> OverallState:
    """Focused researcher agent for single sub-topic.
    
    Specialized researcher that focuses exclusively on one sub-topic to ensure deep, 
    comprehensive coverage without interference from other topics. This targeted approach
    enables higher quality research results for each specific area of investigation.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Format the specialized researcher prompt
    formatted_prompt = RESEARCHER_PROMPT.format(sub_topic=state["topic_name"])
    
    # Use Google Search for this sub-topic
    try:
        response = genai_client.models.generate_content(
            model=configurable.query_generator_model,
            contents=formatted_prompt,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0,
            },
        )
        
        # Safely process citations for this sub-topic
        grounding_chunks = None
        if (response and 
            hasattr(response, 'candidates') and 
            response.candidates and 
            len(response.candidates) > 0 and
            hasattr(response.candidates[0], 'grounding_metadata') and
            response.candidates[0].grounding_metadata and
            hasattr(response.candidates[0].grounding_metadata, 'grounding_chunks')):
            grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks
        
        if grounding_chunks is not None:
            resolved_urls = resolve_urls(grounding_chunks, state["sub_topic_id"])
            citations = get_citations(response, resolved_urls)
            modified_text = insert_citation_markers(response.text, citations) if citations else (response.text if response else "")
            sources_gathered = []
            if citations:
                for citation in citations:
                    if citation and "segments" in citation and citation["segments"]:
                        sources_gathered.extend(citation["segments"])
        else:
            # Fallback when no grounding metadata available
            modified_text = response.text if response and hasattr(response, 'text') else "該当する情報は見つかりませんでした。"
            sources_gathered = []
            
    except Exception as e:
        print(f"🚨 Error in focused_researcher for topic '{state.get('topic_name', 'unknown')}': {e}")
        modified_text = "該当する情報は見つかりませんでした。"
        sources_gathered = []
    
    # Format as structured sub-topic research
    research_result = f"""
## {state["topic_name"]}

{modified_text}

### 情報源
{chr(10).join([f"- [{source['label']}]({source['value']})" for source in sources_gathered[:5]])}
"""
    
    return {
        "parallel_research_results": [research_result],
        "sources_gathered": sources_gathered,
    }


def aggregate_research_results(state: OverallState, config: RunnableConfig):
    """Aggregation node that waits for all parallel research to complete.
    
    This node simply passes through the state after all parallel research is complete.
    It acts as a synchronization point before synthesis.
    """
    # Brief processing to ensure parallel results are properly aggregated
    parallel_results_count = len(state.get("parallel_research_results", []))
    sources_count = len(state.get("sources_gathered", []))
    
    print(f"🔄 Aggregating {parallel_results_count} research results with {sources_count} sources...")
    
    return {
        "current_phase": "researching"  # Single phase update after all parallel research
    }


def synthesizer(state: OverallState, config: RunnableConfig) -> SynthesisState:
    """Synthesizer agent that integrates all parallel research results.
    
    Integration specialist that combines findings from multiple parallel research agents 
    into a single coherent, well-structured report. Ensures logical flow and consistency 
    across different research areas while maintaining comprehensive coverage.
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM for synthesis
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.2,  # Lower temperature for more consistent synthesis
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Combine all research results
    research_results = "\n\n---\n\n".join(state.get("parallel_research_results", []))
    research_question = state.get("structured_plan", {}).get("research_question", get_research_topic(state["messages"]))
    
    # Format synthesizer prompt
    formatted_prompt = SYNTHESIZER_PROMPT.format(
        research_results=research_results,
        research_question=research_question
    )
    
    # Generate draft report
    result = llm.invoke(formatted_prompt)
    
    return {
        "draft_report": result.content,
        "current_phase": "synthesizing"
    }


def critique_agent(state: OverallState, config: RunnableConfig) -> CritiqueState:
    """Critique agent for quality assurance.
    
    Quality assurance specialist that evaluates research reports for accuracy, completeness,
    and overall quality. Provides detailed feedback and recommendations for improvement,
    enabling iterative refinement through a self-correction feedback loop.
    """
    MAX_REVISIONS = 1  # STRICT LIMIT: Match other functions
    current_revisions = state.get("revision_count", 0)
    
    print(f"📝 CRITIQUE START - Current revisions: {current_revisions}/{MAX_REVISIONS}")
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.reflection_model
    
    # Check if we've already reached the revision limit
    if current_revisions >= MAX_REVISIONS:
        print(f"🚫 CRITIQUE: Revision limit already reached ({current_revisions})")
        print(f"🚫 FORCING should_revise=False to prevent infinite loop")
        return {
            "critique_feedback": "品質評価: 修正回数の制限に達したため、現在のレポートで完了します。",
            "should_revise": False,  # FORCE False to prevent infinite loop
            "revision_suggestions": [],
            "current_phase": "critiquing_completed"
        }
    
    # Initialize LLM for critique
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.7,  # Higher temperature for more creative critique
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(CritiqueAssessment)
    
    # Format critique prompt
    draft_report = state.get("draft_report", "")
    formatted_prompt = CRITIQUE_PROMPT.format(draft_report=draft_report)
    
    # Generate critique
    result = structured_llm.invoke(formatted_prompt)
    
    # SAFETY CHECK: Force should_revise to False if we would exceed limit
    original_should_revise = result.should_revise
    if current_revisions >= MAX_REVISIONS:
        result.should_revise = False
        print(f"🛡️ SAFETY: Forced should_revise from {original_should_revise} to False")
    
    print(f"📝 CRITIQUE RESULT: should_revise={result.should_revise} (original: {original_should_revise})")
    print(f"📝 Current revision count: {current_revisions}")
    
    return {
        "critique_feedback": f"品質評価: {result.overall_quality}\n\n強み: {', '.join(result.strengths)}\n\n改善点: {', '.join(result.weaknesses)}\n\n具体的提案: {', '.join(result.specific_suggestions)}",
        "should_revise": result.should_revise,
        "revision_suggestions": result.specific_suggestions,
        "current_phase": "critiquing"
    }


def evaluate_report_quality(state: CritiqueState, config: RunnableConfig):
    """Routing function that determines whether to revise or finalize the report.
    
    Controls the critique loop based on quality assessment with STRICT limits.
    """
    MAX_REVISIONS = 1  # STRICT LIMIT: Only allow 1 revision to prevent infinite loops
    current_revisions = state.get("revision_count", 0)
    should_revise = state.get("should_revise", False)
    
    print(f"🔍 QUALITY EVALUATION - Current revisions: {current_revisions}/{MAX_REVISIONS}")
    print(f"🔍 Should revise: {should_revise}")
    print(f"🔍 State revision_count: {state.get('revision_count', 'NOT_SET')}")
    
    # ABSOLUTE HARD LIMIT: Never exceed 1 revision under any circumstances
    if current_revisions >= MAX_REVISIONS:
        print(f"🚫 REVISION LIMIT REACHED: {current_revisions} >= {MAX_REVISIONS}")
        print(f"🚫 FORCING FINAL POLISH - No more revisions allowed")
        return "final_polish"
    
    # Only proceed with revision if we haven't hit the limit AND should_revise is True
    if should_revise and current_revisions < MAX_REVISIONS:
        print(f"✅ PROCEEDING TO REVISION #{current_revisions + 1}/{MAX_REVISIONS}")
        return "revise_report"
    else:
        print(f"✅ PROCEEDING TO FINAL POLISH (revisions: {current_revisions}, should_revise: {should_revise})")
        return "final_polish"


def revise_report(state: OverallState, config: RunnableConfig) -> SynthesisState:
    """Revises the report based on critique feedback.
    
    Implements SINGLE revision with strict limits to prevent infinite loops.
    """
    MAX_REVISIONS = 1  # STRICT LIMIT: Match the evaluation function
    current_revisions = state.get("revision_count", 0)
    
    print(f"🔄 REVISION START - Current: {current_revisions}/{MAX_REVISIONS}")
    print(f"🔄 State before revision: revision_count = {state.get('revision_count', 'NOT_SET')}")
    
    # CRITICAL SAFETY CHECK: Never allow more than 1 revision
    if current_revisions >= MAX_REVISIONS:
        print(f"🚨 EMERGENCY STOP - Maximum revisions ({current_revisions}) reached")
        print(f"🚨 Aborting revision, returning current draft")
        return {
            "draft_report": state.get("draft_report", ""),
            "revision_count": current_revisions,  # Don't increment
            "current_phase": "emergency_stopped"
        }
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM for revision
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.3,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Create revision prompt incorporating feedback
    revision_prompt = f"""
あなたは専門のレポートライターです。以下のドラフトレポートを、提供された批評フィードバックに基づいて改善してください。

## 批評フィードバック
{state.get("critique_feedback", "")}

## 改善すべき点
{chr(10).join(f"- {suggestion}" for suggestion in state.get("revision_suggestions", []))}

## 現在のドラフト
{state.get("draft_report", "")}

## 指示
- 批評フィードバックを注意深く検討し、指摘された問題を修正してください
- 日本語で自然で読みやすいレポートを作成してください
- マークダウン形式を保持してください
- 引用を適切に維持してください
- 構造と論理的な流れを改善してください

改善されたレポートを提供してください：
"""
    
    # Generate revised report
    result = llm.invoke(revision_prompt)
    
    new_revision_count = current_revisions + 1
    print(f"✅ REVISION COMPLETED - New count: {new_revision_count}/{MAX_REVISIONS}")
    print(f"✅ This was the FINAL allowed revision")
    
    return {
        "draft_report": result.content,
        "revision_count": new_revision_count,
        "current_phase": "revising"
    }


def final_polish(state: OverallState, config: RunnableConfig):
    """Final polishing and completion of the research report.
    
    Applies final touches and saves the completed report.
    """
    # Use the latest draft as the final report
    final_content = state.get("draft_report", "")
    
    # Add completion footer with research summary
    parallel_results_count = len(state.get("parallel_research_results", []))
    sources_count = len(state.get("sources_gathered", []))
    revision_count = state.get("revision_count", 0)
    
    metadata_footer = f"""

---

## 🔬 研究分析レポート完了

**調査サマリー:**
- **並列リサーチセッション**: {parallel_results_count}件
- **収集情報源**: {sources_count}件  
- **品質改善ラウンド**: {revision_count}回（上限1回）

**生成システム**: 高度なマルチエージェント・ディープリサーチフレームワーク  
**生成日時**: {get_current_date()}

---

*本レポートは、専門化されたAIエージェント（プランナー、並列リサーチャー、統合分析官、品質評価官）によって段階的に作成され、厳格な品質管理プロセス（最大1回の修正）を経て完成されました。*
"""
    
    final_content_with_metadata = final_content + metadata_footer
    
    # Save to history (existing functionality)
    try:
        duration_ms = int((time.time() - state.get("start_time", time.time())) * 1000)
        search_queries = [result for result in state.get("parallel_research_results", [])]
        sources_count = len(state.get("sources_gathered", []))
        
        history_id = history_manager.save_history(
            query=state.get("original_query", get_research_topic(state["messages"])),
            effort=state.get("effort_level", "comprehensive"),
            model=state.get("reasoning_model", "gemini-2.5-pro"),
            result=final_content_with_metadata,
            search_queries=search_queries[:10],  # Limit to avoid excessive storage
            sources_count=sources_count,
            duration_ms=duration_ms
        )
        
        print(f"Enhanced research completed and saved: {history_id}")
        
    except Exception as e:
        print(f"History save error in enhanced research: {e}")

    return {
        "messages": [AIMessage(content=final_content_with_metadata)],
        "final_report": final_content_with_metadata,
        "current_phase": "completed"
    }


# Original nodes (preserved for backward compatibility)
def create_research_plan(state: OverallState, config: RunnableConfig) -> ResearchPlanState:
    """LangGraph node that creates a structured research plan based on the user's question.
    
    This implements Step 1 of the DeepResearch algorithm: Query Input and Research Plan Creation.
    Creates a strategic outline for the research report that will guide subsequent information gathering.
    
    Args:
        state: Current graph state containing the user's question
        config: Configuration for the runnable, including LLM provider settings
    
    Returns:
        Dictionary with state update, including research_plan containing sections and rationale
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Initialize Gemini 2.5 Pro for plan creation
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0.3,  # Lower temperature for more structured planning
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(ResearchPlan)
    
    # Format the prompt for research plan creation
    current_date = get_current_date()
    formatted_prompt = research_plan_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
    )
    
    # Generate the research plan
    result = structured_llm.invoke(formatted_prompt)
    
    # メタデータの初期化
    original_query = get_research_topic(state["messages"])
    effort_level = "medium"  # デフォルト値、実際の値はフロントエンドから渡される
    
    return {
        "research_plan": {
            "sections": result.sections,
            "rationale": result.rationale
        },
        "plan_approved": True,
        "start_time": time.time(),
        "original_query": original_query,
        "effort_level": effort_level
    }


def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses Gemini 2.5 Pro to create an optimized search queries for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated queries
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # init Gemini 2.5 Pro
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt - now uses Japanese instructions by default
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"search_query": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using the native Google Search API tool.

    Executes a web search using the native Google Search API tool in combination with Gemini 2.5 Pro.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Configure
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    # Uses the google genai client as the langchain client doesn't return grounding metadata
    try:
        response = genai_client.models.generate_content(
            model=configurable.query_generator_model,
            contents=formatted_prompt,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0,
            },
        )
        
        # Safely process citations
        grounding_chunks = None
        if (response and 
            hasattr(response, 'candidates') and 
            response.candidates and 
            len(response.candidates) > 0 and
            hasattr(response.candidates[0], 'grounding_metadata') and
            response.candidates[0].grounding_metadata and
            hasattr(response.candidates[0].grounding_metadata, 'grounding_chunks')):
            grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks
        
        if grounding_chunks is not None:
            resolved_urls = resolve_urls(grounding_chunks, state["id"])
            citations = get_citations(response, resolved_urls)
            modified_text = insert_citation_markers(response.text, citations) if citations else (response.text if response else "")
            sources_gathered = []
            if citations:
                for citation in citations:
                    if citation and "segments" in citation and citation["segments"]:
                        sources_gathered.extend(citation["segments"])
        else:
            # Fallback when no grounding metadata available
            modified_text = response.text if response and hasattr(response, 'text') else "該当する情報は見つかりませんでした。"
            sources_gathered = []
            
    except Exception as e:
        print(f"🚨 Error in web_research for query '{state.get('search_query', 'unknown')}': {e}")
        modified_text = "該当する情報は見つかりませんでした。"
        sources_gathered = []

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # Deep Research approach - structured reflection with comprehensive analysis
    reflection_instructions = """
あなたは高度な調査エージェントです。収集したウェブ調査の要約を評価し、構造化された深層調査手法に従って知識のギャップを特定し、戦略的な追加質問を作成することがあなたのタスクです。

## 段階的な分析プロセス

1. **調査の方向性の確認**: 現在の日付（{current_date}）を考慮し、トピック「{research_topic}」の性質を判断してください：
   - 過去の出来事：確定した事実と結果を中心に分析
   - 現在進行中：最新の動向と現状を重視
   - 未来の予測：発表済み情報と専門家の分析を重視
   - 複合的トピック：複数の視点から多面的に分析

2. **多角的な情報整理**: トピックの性質に応じて、以下の要素で情報を整理してください：
   - **基本情報と背景**: 概要、歴史的経緯、重要性
   - **現状分析**: 最新の状況、データ、事実関係
   - **多角的視点**: 異なるステークホルダーの視点、様々な側面
   - **影響と意義**: 社会的、経済的、技術的インパクト
   - **将来展望**: 予測可能な発展、課題、機会

3. **段階的な内容評価**: 以下の構造で現在の調査内容を評価してください：
   - 基本的な事実関係は網羅されているか？
   - 現状の動向と最新情報は十分か？
   - 複数の視点からの分析が含まれているか？
   - 社会的・経済的影響の分析は適切か？
   - 将来の展望と課題は明確化されているか？

4. **信頼できる情報源の評価**: 以下の信頼性の高い情報源からの情報が十分含まれているか確認してください：
   - 関連する公式サイト・組織（政府機関、企業公式サイト、学術機関）
   - 主要メディア（NHK、朝日新聞、日経新聞、Reuters、BBC等）
   - 業界専門機関・サイト（業界団体、専門誌、シンクタンク）

5. **知識ギャップの特定**: 上記の分析に基づき、まだ不足している重要な情報は何ですか？トピックの本質を理解するために、どの側面をより深く調査する必要がありますか？

6. **戦略的追加クエリの作成**: これらのギャップを埋めるために、的確で分析的な追加の検索クエリのリストを日本語で作成してください。これらのクエリは、単なる事実情報ではなく、深い洞察、多角的な分析、長期的な影響を明らかにすることを目的としてください。

現在の日付: {current_date}

調査要約:
{summaries}
"""

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    # init Reasoning Model
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Deep Research approach - comprehensive structured analysis report
    answer_instructions = """
あなたは高度な調査エージェントです。調査トピック「{research_topic}」について、構造化された深層調査手法に基づいて、深く包括的な分析レポートを作成してください。

**調査の方向性の明示**:
まず、現在の日付（{current_date}）を考慮して調査の方向性を明確にしてください：
- 過去の出来事：確定した事実と結果を中心とした分析
- 現在進行中：最新の動向と現状を重視した分析
- 未来の予測：発表済み情報と専門家の分析に基づく分析
- 複合的トピック：複数の視点から多面的な分析

**段階的な情報整理とレポート構成**:
以下のセクション構成に従って、段階的で包括的な分析レポートを作成してください：
{research_plan_sections}

トピックの性質に応じて、以下の要素を適切に組み合わせて構成してください：
1. **基本情報と背景** - トピックの概要、歴史的経緯、重要性
2. **現状分析** - 最新の状況、データ、事実関係
3. **多角的視点** - 異なるステークホルダーの視点、様々な側面からの分析
4. **影響と意義** - 社会的、経済的、技術的インパクト
5. **将来の展望** - 予測可能な発展、課題、機会

**レポート作成指示**:
1. **マークダウン形式**: 完全なマークダウン形式でレポートを作成してください。適切な見出し階層（#, ##, ###）、リスト、強調（**bold**）、引用を活用してください。

2. **段階的な思考プロセスの反映**: 構造化された深層調査手法に従い、調査の過程と発見を段階的に整理してください：
   - 調査結果の概要
   - 主要な発見事項の整理
   - 詳細分析（深い洞察、多角的な視点）
   - 将来展望と示唆

3. **信頼できる情報源の重視**: 以下の信頼性の高い情報源を重視し、情報の信頼性を示してください：
   - 関連する公式サイト・組織（政府機関、企業公式サイト、学術機関）
   - 主要メディア（NHK、朝日新聞、日経新聞、Reuters、BBC等）
   - 業界専門機関・サイト（業界団体、専門誌、シンクタンク）

4. **具体的なデータと事実**: 可能な限り具体的な日付、数値、名称、データを含めてください。

5. **深い洞察の提供**: 単なる事実の羅列ではなく、以下を含む深い分析を提供してください：
   - **背景と文脈の分析**: なぜこの状況が生じているのか？
   - **多角的視点**: 異なるステークホルダーからの視点
   - **影響と意義**: 社会、経済、技術への長期的インパクト
   - **課題と機会**: 今後の課題と発展の可能性

6. **情報源の活用**: 
   - 提供された引用マーカー（[1], [2]など）を適切に使用
   - 複数の情報源から得られた洞察を統合
   - 情報の日付を確認し、いつの情報かを明記

7. **批判的思考**: 
   - 情報の信頼性を評価
   - 複数の情報源を比較
   - バランスの取れた見解を提供

8. **日本語での出力**: 全てのアウトプットは自然で読みやすい日本語で作成してください。

**現在の日付**: {current_date}

**分析対象の調査結果**:
{summaries}

**重要**: このレポートは、構造化された深層調査手法に基づく段階的で体系的な思考プロセスを反映し、包括的でありながら構造化された分析レポートとして作成してください。常に批判的思考を用い、複数の情報源を比較し、バランスの取れた見解を提供してください。
"""

    # Format the prompt with research plan sections
    current_date = get_current_date()
    research_plan_sections = ""
    if state.get("research_plan") and "sections" in state["research_plan"]:
        research_plan_sections = "\n".join([f"- {section}" for section in state["research_plan"]["sections"]])
    else:
        # Fallback if no research plan exists
        research_plan_sections = "- エグゼクティブサマリー\n- 主要発表内容の分析\n- 戦略的意味と競合への影響\n- 将来展望と示唆"
    
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        research_plan_sections=research_plan_sections,
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # init Reasoning Model, default to Gemini 2.5 Pro
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    # Replace the short urls with the original urls and add all used urls to the sources_gathered
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    # 検索履歴を保存
    try:
        duration_ms = int((time.time() - state.get("start_time", time.time())) * 1000) if state.get("start_time") else None
        search_queries = state.get("search_query", [])
        sources_count = len(unique_sources)
        
        history_id = history_manager.save_history(
            query=state.get("original_query", get_research_topic(state["messages"])),
            effort=state.get("effort_level", "medium"),
            model=reasoning_model,
            result=result.content,
            search_queries=search_queries,
            sources_count=sources_count,
            duration_ms=duration_ms
        )
        
        print(f"検索履歴を保存しました: {history_id}")
        
    except Exception as e:
        print(f"検索履歴の保存中にエラーが発生しました: {e}")

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# Enhanced Multi-Agent Deep Research Graph (Primary Implementation)
enhanced_builder = StateGraph(OverallState, config_schema=Configuration)

# Add all enhanced multi-agent nodes
enhanced_builder.add_node("enhanced_planner", enhanced_planner)
enhanced_builder.add_node("focused_researcher", focused_researcher)
enhanced_builder.add_node("aggregate_research_results", aggregate_research_results)
enhanced_builder.add_node("synthesizer", synthesizer)
enhanced_builder.add_node("critique_agent", critique_agent)
enhanced_builder.add_node("revise_report", revise_report)
enhanced_builder.add_node("final_polish", final_polish)

# Build the enhanced multi-agent workflow using hierarchical planning and parallel execution:
# START -> Enhanced Planner -> Parallel Research -> Synthesis -> Critique -> (Revise or Polish) -> END

# Entry point: Enhanced hierarchical planning
enhanced_builder.add_edge(START, "enhanced_planner")

# Parallel research branches (dispatched directly from planner)
enhanced_builder.add_conditional_edges(
    "enhanced_planner", 
    run_parallel_research,
    ["focused_researcher"]
)

# All parallel research results flow to aggregator
enhanced_builder.add_edge("focused_researcher", "aggregate_research_results")

# Aggregator synchronizes and then flows to synthesizer
enhanced_builder.add_edge("aggregate_research_results", "synthesizer")

# Synthesizer creates draft, then goes to critique
enhanced_builder.add_edge("synthesizer", "critique_agent")

# Critique decides: revise or finalize
enhanced_builder.add_conditional_edges(
    "critique_agent", 
    evaluate_report_quality, 
    ["revise_report", "final_polish"]
)

# Revision loop back to critique
enhanced_builder.add_edge("revise_report", "critique_agent")

# Final polish leads to END
enhanced_builder.add_edge("final_polish", END)

# Compile enhanced graph
enhanced_graph = enhanced_builder.compile(name="enhanced-deepresearch-agent")


# Original Simple Graph (Preserved for backward compatibility)
simple_builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes implementing the 5-step DeepResearch algorithm
simple_builder.add_node("create_research_plan", create_research_plan)  # Step 1: Research Plan Creation
simple_builder.add_node("generate_query", generate_query)              # Step 2: Initial Query Generation  
simple_builder.add_node("web_research", web_research)                  # Step 2: Web Research
simple_builder.add_node("reflection", reflection)                      # Step 3: Reflection & Knowledge Gap Analysis
simple_builder.add_node("finalize_answer", finalize_answer)            # Step 4: Final Documentation

# Build the simple workflow
simple_builder.add_edge(START, "create_research_plan")
simple_builder.add_edge("create_research_plan", "generate_query")
simple_builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
simple_builder.add_edge("web_research", "reflection")
simple_builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
simple_builder.add_edge("finalize_answer", END)

simple_graph = simple_builder.compile(name="simple-deepresearch-agent")

# ============================================================================
# ACADEMIC RESEARCH FRAMEWORK AGENTS (学術論文フレームワーク用エージェント)
# ============================================================================

def academic_background_generator(state: OverallState, config: RunnableConfig) -> AcademicBackgroundState:
    """学術的背景と目的を生成するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.1,  # Low temperature for factual accuracy
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AcademicBackground)
    
    # Get research question
    research_question = get_research_topic(state["messages"])
    
    # Format prompt
    formatted_prompt = ACADEMIC_BACKGROUND_PROMPT.format(research_question=research_question)
    
    # Generate background and objective
    result = structured_llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Academic background generated: {result.background[:100]}...")
    
    return {
        "background": result.background,
        "objective": result.objective,
        "research_framework": result.research_framework
    }


def academic_framework_planner(state: OverallState, config: RunnableConfig) -> AcademicFrameworkState:
    """学術論文の全体フレームワークを作成するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.2,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Format background and objective
    background_data = state.get("academic_background", {})
    background_and_objective = f"""
## 背景
{background_data.get('background', '')}

## 目的
{background_data.get('objective', '')}

## 研究フレームワーク
{background_data.get('research_framework', '')}
    """
    
    # Format prompt
    formatted_prompt = ACADEMIC_FRAMEWORK_PROMPT.format(
        background_and_objective=background_and_objective
    )
    
    # Generate framework
    result = llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Academic framework generated: {len(result.content)} characters")
    
    # Parse the markdown response into sections (simplified parsing)
    content = result.content
    sections = {
        "introduction": "",
        "objective": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "conclusion": ""
    }
    
    # Simple section extraction (this could be improved with better parsing)
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if '背景' in line or 'introduction' in line_lower:
            current_section = 'introduction'
        elif '目的' in line or 'objective' in line_lower:
            current_section = 'objective'
        elif '方法' in line or 'methods' in line_lower:
            current_section = 'methods'
        elif '結果' in line or 'results' in line_lower:
            current_section = 'results'
        elif '考察' in line or 'discussion' in line_lower:
            current_section = 'discussion'
        elif '結論' in line or 'conclusion' in line_lower:
            current_section = 'conclusion'
        elif current_section and line.strip():
            sections[current_section] += line + '\n'
    
    return sections


def academic_abstract_generator(state: OverallState, config: RunnableConfig) -> AcademicAbstractState:
    """学術論文のアブストラクトを生成するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.1,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AcademicAbstract)
    
    # Create full paper draft from framework
    framework = state.get("academic_framework", {})
    full_paper_draft = f"""
# 学術論文ドラフト

## 背景
{framework.get('introduction', '')}

## 目的
{framework.get('objective', '')}

## 材料と方法
{framework.get('methods', '')}

## 結果
{framework.get('results', '')}

## 考察
{framework.get('discussion', '')}

## 結論
{framework.get('conclusion', '')}
    """
    
    # Format prompt
    formatted_prompt = ABSTRACT_GENERATOR_PROMPT.format(full_paper_draft=full_paper_draft)
    
    # Generate abstract
    result = structured_llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Academic abstract generated: {len(result.abstract_text)} characters")
    
    return {
        "abstract_text": result.abstract_text,
        "key_findings": result.key_findings
    }


def literature_researcher(state: OverallState, config: RunnableConfig) -> LiteratureResearchState:
    """先行研究・文献調査を実施するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.1,  # Very low temperature for factual research
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(LiteratureResearch)
    
    # Get abstract for research
    abstract_data = state.get("academic_abstract", "")
    
    # Perform web search for literature
    research_question = get_research_topic(state["messages"])
    
    # Create focused search queries for academic sources
    academic_queries = [
        f"{research_question} 学術研究 論文",
        f"{research_question} 公式データ 統計",
        f"{research_question} 政府発表 公式情報"
    ]
    
    search_results = []
    for i, query in enumerate(academic_queries):
        try:
            # Use existing Google Search API functionality
            response = genai_client.models.generate_content(
                model=reasoning_model,
                contents=f"以下のトピックについて、信頼性の高い学術的情報源から事実情報を調査してください: {query}",
                config={
                    "tools": [{"google_search": {}}],
                    "temperature": 0.1,
                },
            )
            
            # Process search results safely
            if response and response.text:
                # Resolve URLs and get citations like in web_research
                if (hasattr(response, 'candidates') and 
                    response.candidates and 
                    len(response.candidates) > 0):
                    candidate = response.candidates[0]
                    if (hasattr(candidate, 'grounding_metadata') and 
                        candidate.grounding_metadata and 
                        hasattr(candidate.grounding_metadata, 'grounding_chunks') and
                        candidate.grounding_metadata.grounding_chunks is not None):
                        try:
                            resolved_urls = resolve_urls(candidate.grounding_metadata.grounding_chunks, i)
                            citations = get_citations(response, resolved_urls) if resolved_urls else None
                            if citations:
                                modified_text = insert_citation_markers(response.text, citations)
                            else:
                                modified_text = response.text
                            search_results.append(f"検索クエリ: {query}\n結果: {modified_text}\n---")
                        except Exception as citation_error:
                            print(f"Citation processing failed for '{query}': {citation_error}")
                            search_results.append(f"検索クエリ: {query}\n結果: {response.text}\n---")
                    else:
                        search_results.append(f"検索クエリ: {query}\n結果: {response.text}\n---")
                else:
                    search_results.append(f"検索クエリ: {query}\n結果: {response.text}\n---")
        except Exception as e:
            print(f"Literature search failed for '{query}': {e}")
            search_results.append(f"検索クエリ: {query}\nエラー: 検索に失敗しました\n---")
    
    combined_search_results = "\n".join(search_results)
    
    # Format prompt with search results
    formatted_prompt = LITERATURE_RESEARCH_PROMPT.format(
        research_abstract=abstract_data
    ) + f"\n\n### 検索結果:\n{combined_search_results}"
    
    # Generate literature research
    result = structured_llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Literature research completed: {len(result.factual_findings)} facts found")
    
    return {
        "factual_findings": result.factual_findings,
        "official_data": result.official_data,
        "reliable_sources": result.reliable_sources,
        "source_urls": result.source_urls
    }


def academic_synthesizer(state: OverallState, config: RunnableConfig):
    """最終的な学術論文を統合・作成するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.2,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Prepare data
    abstract_data = state.get("academic_abstract", "")
    literature_data = state.get("literature_research", {})
    
    # Format literature research
    literature_summary = f"""
## 先行研究調査結果

### 主要な事実情報
{chr(10).join(f"- {fact}" for fact in literature_data.get('factual_findings', []))}

### 関連する公式データ
{chr(10).join(f"- {data}" for data in literature_data.get('official_data', []))}

### 信頼性の高い情報源
{chr(10).join(f"- {source}" for source in literature_data.get('reliable_sources', []))}

### 参考URL
{chr(10).join(f"- {url}" for url in literature_data.get('source_urls', []))}
    """
    
    # Format prompt
    formatted_prompt = ACADEMIC_REPORT_SYNTHESIS_PROMPT.format(
        research_abstract=abstract_data,
        literature_research=literature_summary
    )
    
    # Generate final academic report
    result = llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Academic report synthesized: {len(result.content)} characters")
    
    return {
        "academic_draft": result.content,
        "current_phase": "academic_synthesis_completed"
    }


def academic_reviewer(state: OverallState, config: RunnableConfig) -> AcademicReviewState:
    """学術論文のレビューを実施するエージェント"""
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.reflection_model
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0.3,  # Slightly higher temperature for critical analysis
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AcademicReview)
    
    # Get academic draft for review
    academic_draft = state.get("academic_draft", "")
    
    # Format prompt
    formatted_prompt = ACADEMIC_REVIEW_PROMPT.format(academic_draft=academic_draft)
    
    # Generate review
    result = structured_llm.invoke(formatted_prompt)
    
    print(f"DEBUG - Academic review completed: revision_needed={result.revision_needed}")
    
    return {
        "overall_assessment": result.overall_assessment,
        "specific_improvements": result.specific_improvements,
        "speculation_issues": result.speculation_issues,
        "revision_needed": result.revision_needed,
        "revision_instructions": result.revision_instructions
    }


# ============================================================================
# ACADEMIC RESEARCH FRAMEWORK GRAPH (学術論文フレームワーク用グラフ)
# ============================================================================

def build_academic_research_graph():
    """学術論文フレームワークに基づく新しいグラフを構築"""
    from langgraph.graph import StateGraph, START, END
    
    # Initialize academic research graph
    academic_builder = StateGraph(OverallState)
    
    # Add academic research nodes
    academic_builder.add_node("academic_background_generator", academic_background_generator)
    academic_builder.add_node("academic_framework_planner", academic_framework_planner) 
    academic_builder.add_node("academic_abstract_generator", academic_abstract_generator)
    academic_builder.add_node("literature_researcher", literature_researcher)
    academic_builder.add_node("academic_synthesizer", academic_synthesizer)
    academic_builder.add_node("academic_reviewer", academic_reviewer)
    
    # Build academic research flow
    academic_builder.add_edge(START, "academic_background_generator")
    academic_builder.add_edge("academic_background_generator", "academic_framework_planner")
    academic_builder.add_edge("academic_framework_planner", "academic_abstract_generator")
    academic_builder.add_edge("academic_abstract_generator", "literature_researcher")
    academic_builder.add_edge("literature_researcher", "academic_synthesizer")
    academic_builder.add_edge("academic_synthesizer", "academic_reviewer")
    academic_builder.add_edge("academic_reviewer", END)
    
    return academic_builder.compile(name="academic-research-agent")


# Build academic research graph
academic_graph = build_academic_research_graph()

# Export enhanced graph as primary (for general research queries)
# Use enhanced_graph for casual research, academic_graph for academic papers
graph = enhanced_graph