from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import add_messages
from typing_extensions import Annotated


import operator


class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    reasoning_model: str
    research_plan: dict  # Contains sections and rationale
    plan_approved: bool
    # 履歴保存用のメタデータ
    start_time: float  # 実行開始時刻
    effort_level: str  # low/medium/high
    original_query: str  # ユーザーの元のクエリ
    
    # Enhanced multi-agent architecture fields
    structured_plan: dict  # Detailed plan with sub-topics and queries
    parallel_research_results: Annotated[list, operator.add]  # Results from parallel research
    draft_report: str  # Initial synthesized report
    critique_feedback: str  # Feedback from critique agent
    final_report: str  # Final polished report
    revision_count: int  # Number of revisions performed
    current_phase: str  # Track current phase: 'planning', 'researching', 'synthesizing', 'critiquing', 'finalizing'
    
    # Academic research framework state fields
    academic_background: dict  # Background and objective from academic analysis
    academic_framework: dict  # Complete academic paper framework
    academic_abstract: str  # Generated abstract
    literature_research: dict  # Literature research results
    academic_draft: str  # Academic paper draft
    academic_review: dict  # Academic review results


class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int


# Enhanced state classes for multi-agent architecture
class PlannerState(TypedDict):
    research_question: str
    sub_topics: list[dict]  # List of SubTopic dicts
    estimated_depth: str


class ParallelResearchState(TypedDict):
    topic_name: str
    search_queries: list[str]
    research_result: str
    sources_used: list[str]
    sub_topic_id: str


class SynthesisState(TypedDict):
    research_question: str
    research_results: list[str]  # Combined results from all parallel research
    draft_report: str


class CritiqueState(TypedDict):
    draft_report: str
    critique_feedback: str
    should_revise: bool
    revision_suggestions: list[str]


class ResearchPlanState(TypedDict):
    sections: list[str]
    rationale: str


# ============================================================================
# ACADEMIC RESEARCH FRAMEWORK STATE CLASSES (学術論文フレームワーク用状態クラス)
# ============================================================================

class AcademicBackgroundState(TypedDict):
    """学術的背景と目的の状態"""
    background: str
    objective: str
    research_framework: str


class AcademicFrameworkState(TypedDict):
    """学術論文フレームワークの状態"""
    introduction: str
    objective: str
    methods: str
    results: str
    discussion: str
    conclusion: str


class AcademicAbstractState(TypedDict):
    """学術アブストラクトの状態"""
    abstract_text: str
    key_findings: list[str]


class LiteratureResearchState(TypedDict):
    """先行研究調査の状態"""
    factual_findings: list[str]
    official_data: list[str]
    reliable_sources: list[str]
    source_urls: list[str]


class AcademicReviewState(TypedDict):
    """学術レビューの状態"""
    overall_assessment: str
    specific_improvements: list[str]
    speculation_issues: list[str]
    revision_needed: bool
    revision_instructions: list[str]


class Query(TypedDict):
    query: str
    rationale: str


class QueryGenerationState(TypedDict):
    search_query: list[Query]


class WebSearchState(TypedDict):
    search_query: str
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    running_summary: str = field(default=None)  # Final report
