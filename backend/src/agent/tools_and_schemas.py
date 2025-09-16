from typing import List, Dict, Any
from pydantic import BaseModel, Field


# Enhanced schemas for multi-agent deep research architecture
class SubTopic(BaseModel):
    """Single research sub-topic with focused search queries."""
    topic_name: str = Field(
        description="Name of the specific sub-topic to research"
    )
    search_queries: List[str] = Field(
        description="List of focused search queries for this sub-topic"
    )


class StructuredResearchPlan(BaseModel):
    """Comprehensive research plan with hierarchical structure."""
    research_question: str = Field(
        description="The original high-level research question from the user"
    )
    sub_topics: List[SubTopic] = Field(
        description="List of sub-topics, each with focused search queries"
    )
    estimated_depth: str = Field(
        description="Expected depth of research: 'basic', 'comprehensive', or 'exhaustive'"
    )


class ResearchPlan(BaseModel):
    """Schema for the research plan with structured outline."""
    sections: List[str] = Field(
        description="A list of section titles for the research report structure."
    )
    rationale: str = Field(
        description="Explanation of why these sections will provide comprehensive coverage of the topic."
    )


class SearchQueryList(BaseModel):
    query: List[str] = Field(
        description="A list of search queries to be used for web research."
    )
    rationale: str = Field(
        description="A brief explanation of why these queries are relevant to the research topic."
    )


class SubTopicResearch(BaseModel):
    """Results from researching a single sub-topic."""
    topic_name: str = Field(
        description="Name of the researched sub-topic"
    )
    summary: str = Field(
        description="Comprehensive summary of findings for this sub-topic"
    )
    key_findings: List[str] = Field(
        description="List of key findings or insights"
    )
    sources_used: List[str] = Field(
        description="List of source URLs used for this research"
    )


class CitedAnswer(BaseModel):
    """Answer with proper citations to sources."""
    answer: str = Field(
        description="The complete answer based solely on provided sources"
    )
    citations: List[int] = Field(
        description="List of source IDs used to support the answer"
    )


class CritiqueAssessment(BaseModel):
    """Critique assessment of a research report."""
    overall_quality: str = Field(
        description="Overall assessment: 'excellent', 'good', 'needs_improvement', or 'poor'"
    )
    strengths: List[str] = Field(
        description="List of strengths in the current report"
    )
    weaknesses: List[str] = Field(
        description="List of weaknesses or areas for improvement"
    )
    specific_suggestions: List[str] = Field(
        description="Specific actionable suggestions for improvement"
    )
    should_revise: bool = Field(
        description="Whether the report should be revised"
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the provided summaries are sufficient to answer the user's question."
    )
    knowledge_gap: str = Field(
        description="A description of what information is missing or needs clarification."
    )
    follow_up_queries: List[str] = Field(
        description="A list of follow-up queries to address the knowledge gap."
    )


# ============================================================================
# ACADEMIC RESEARCH FRAMEWORK SCHEMAS (学術論文フレームワーク用スキーマ)
# ============================================================================

class AcademicBackground(BaseModel):
    """学術的背景と目的のスキーマ"""
    background: str = Field(
        description="学術的な背景の記述（事実のみ、推測・見解は含まない）"
    )
    objective: str = Field(
        description="明確な調査目的の記述（測定可能で検証可能）"
    )
    research_framework: str = Field(
        description="この調査に適用する学術的アプローチの説明"
    )


class AcademicFramework(BaseModel):
    """学術論文の全体フレームワークスキーマ"""
    introduction: str = Field(
        description="背景セクションの内容"
    )
    objective: str = Field(
        description="目的セクションの内容"
    )
    methods: str = Field(
        description="材料と方法セクションの内容"
    )
    results: str = Field(
        description="結果セクションの内容（推定値含む）"
    )
    discussion: str = Field(
        description="考察セクションの内容"
    )
    conclusion: str = Field(
        description="結論セクションの内容"
    )


class AcademicAbstract(BaseModel):
    """学術論文のアブストラクトスキーマ"""
    abstract_text: str = Field(
        description="200-300文字のアブストラクト（推定値を含まない）"
    )
    key_findings: List[str] = Field(
        description="主要な発見のリスト"
    )


class LiteratureResearch(BaseModel):
    """先行研究・文献調査結果のスキーマ"""
    factual_findings: List[str] = Field(
        description="確認された事実情報のリスト"
    )
    official_data: List[str] = Field(
        description="公式データのリスト"
    )
    reliable_sources: List[str] = Field(
        description="信頼性の高い情報源のリスト"
    )
    source_urls: List[str] = Field(
        description="参照したURL情報源のリスト"
    )


class AcademicReview(BaseModel):
    """学術論文レビュー結果のスキーマ"""
    overall_assessment: str = Field(
        description="論文全体の学術的品質評価"
    )
    specific_improvements: List[str] = Field(
        description="具体的な改善点のリスト"
    )
    speculation_issues: List[str] = Field(
        description="推測・見解の問題箇所の指摘"
    )
    revision_needed: bool = Field(
        description="修正が必要かどうか"
    )
    revision_instructions: List[str] = Field(
        description="修正指示のリスト"
    )
