# ディープリサーチエージェントの設計：反復ループからマルチエージェント統合へ LangGraphを用いた実装ガイド

## エグゼクティブサマリー

本レポートは、Gemini Fullstack LangGraph Quickstartを、高度なディープリサーチエージェントへと昇華させるための、段階的な技術ガイドを提供することを目的としています。分析の中心は、単一の反復型エージェントから、スーパーバイザー・ワーカーパラダイムに基づくマルチエージェントシステムへのアーキテクチャ転換です。

この進化の核となるのは、状態管理（ステートマネジメント）、専門化されたプロンプトエンジニアリング、そして信頼性の高い強力なリサーチツールを構築するための制御メカニズム（批評ループ、ヒューマンインザループ）の導入です。本ガイドは、開発者がgraph.pyとprompts.pyを具体的にリファクタリングし、構造化された計画、並列化されたリサーチ、批判的評価、そして検証可能な引用情報を伴う一貫した統合レポート生成が可能なエージェントを構築するための、実践的な設計図を提示します。

---

## セクション1: 基盤となるリサーチ・ループの解体

  

高度なアーキテクチャを構築する前に、まず出発点となる既存のアプリケーションの構造と、その内在的な限界を正確に理解することが不可欠です。

  

### 1.1. gemini-fullstack-langgraph-quickstartのベースラインアーキテクチャ

  

Gemini Fullstack LangGraph Quickstartプロジェクトは、LangGraphを用いたフルスタックAIアプリケーションの優れた入門例です 。そのバックエンドエージェントのコアロジックは、明確な周期的プロセスに基づいています。「初期クエリの生成 → ウェブリサーチ → 結果の考察と知識ギャップの分析 → 反復的な改良」というサイクルです 。

graph.pyで定義されているグラフ構造は、このロジックを直接的に実装したものです。グラフは、generate_query、web_search、reflection、finalize_answerといった一連のノード（処理ステップ）で構成されています 2。これらのノードは条件付きエッジ（分岐）によって接続され、設定された最大反復回数に達するまでループを形成します 。このシンプルな単一エージェントによるループ構造は、基本的なクエリに対しては有効ですが、ディープリサーチに求められる複雑性には対応できません。

同様に、prompts.pyに含まれるプロンプトも、汎用的な目的で設計されています。検索クエリを生成し、その結果を考察するための一般的な指示が含まれていますが、ディープリサーチが要求するような、計画、調査、統合といった複雑なサブタスクに応じた役割の専門化が欠如しています。

  

### 1.2. ディープリサーチにおける中心的限界の特定

  

ベースラインアーキテクチャは堅実な出発点ですが、ディープリサーチの要求水準にはいくつかの根本的な限界があります。

- スケーラビリティのボトルネック: 検索プロセスが反復的かつ逐次的であるため、非効率です。AIが持つ独自の利点の一つは、「多数の検索を並行して開始」できる能力にありますが、ベースラインアーキテクチャはこの機会を活かせていません 3。
    
- 認知的過負荷: 計画、検索、統合という複数の責務を単一のエージェントが担うと、タスクの複雑性が増すにつれてその効率は低下します。生のリサーチ結果がコンテキストウィンドウを肥大化させ、「長期コンテキストの失敗モード」を引き起こす可能性があります 4。
    
- 構造化された計画の欠如: エージェントは検索クエリのフラットなリストを生成するだけであり、人間が主導するディープリサーチの基本である階層的なリサーチ計画やアウトラインを作成しません 5。これにより、調査が体系的でなくなり、表層的なものに留まる危険性があります。
    
- 表層的な統合: finalize_answerノードは、収集されたテキストを単純に統合するだけです。批判的な評価や構造化された執筆プロセスが欠けているため、十分に論証されたレポートではなく、単なる要約になってしまう可能性があります。
    

これらの限界は、単なる最適化の問題ではなく、アーキテクチャそのものが持つ能力の上限を示唆しています。単一エージェントのループ構造は、計画、並列実行、統合といったプロセスを単一の思考プロセス内で管理しようと試みます。これは、プロジェクト計画やバージョン管理なしに一人の開発者が複雑なソフトウェアプロジェクトを管理しようとするようなものです。ディープリサーチは、本質的にタスクを並列化可能なサブトピックに分解することを要求します 4。単一エージェント内で並列化を試みると、すべての検索結果を一つのコンテキストウィンドウに押し戻し、同じエージェントに処理させることになります 4。これは必然的にコンテキストウィンドウの限界、焦点の喪失、そして個々のサブトピックに関する深い推論能力の低下につながります。したがって、並列かつ独立した調査ラインとその後の高次の統合を必要とするタスクに対して、単一ループアーキテクチャは構造的に不向きです。この理解が、マルチエージェントシステムへの移行を単なる改善ではなく、必然的な選択とする根拠となります。

---

## セクション2: エージェントアーキテクチャの進化：ディープリサーチのための3つのパターン

  

エージェントの能力を段階的に向上させるため、ここでは実践的な3つのアーキテクチャパターンを提示します。これにより、複雑性と能力を漸進的に高めることが可能になります。

  

### 2.1. パターン1: 自己修正型リサーチャー（生成・批評ループ）

  

- 概念: これは最初の進化的ステップです。単に最終回答を生成するのではなく、批評と改良のループを導入します。このパターンでは、「生成者（generator）」ノードがドラフトを作成し、「考察者（reflector）」または「批評家（critic）」ノードが特定の基準に基づいてそれを評価します 7。
    
- graph.pyでの実装:
    

- 新しいノードcritique_reportを追加します。
    
- finalize_answer（draft_reportに改名）からのエッジは、critique_reportに向かうよう変更します。
    
- critique_reportから新たな条件付きエッジを追加します。批評の出力（例：「合格」または「不合格」のスコア）に基づき、グラフはdraft_reportに差し戻して再試行するか（批評を新たなコンテキストとして渡す）、新しいfinal_reportノードに進み、ENDに接続します 10。
    

- prompts.pyでの実装:
    

- 新しいプロンプトCRITIQUE_PROMPTを作成します。このプロンプトは、LLMに批評的なレビューワーとして振る舞うよう指示し、ドラフトの事実の正確性、論理的一貫性、完全性、明瞭性をチェックさせます 8。
    

  

### 2.2. パターン2: 階層型リサーチチーム（スーパーバイザー・ワーカーモデル）

  

- 概念: これは最も先進的で堅牢なパターンであり、現実世界のリサーチチームを模倣しています。「スーパーバイザー」エージェントが、専門化された「ワーカー」エージェントのチームを統括します 4。このアーキテクチャは、並列化可能なサブタスクに分解できる複雑なタスクに非常に優れています 4。
    
- アーキテクチャ上の役割:
    

- スーパーバイザー／プランナー: ユーザーのクエリを受け取り、構造化されたリサーチ計画（例：サブトピックを含むアウトライン）を作成し、タスクをリサーチャーエージェントに委任し、完了したリサーチ結果を統合エージェントにルーティングします 6。
    
- リサーチャーエージェント: スーパーバイザーから単一の、焦点が絞られたサブトピックを受け取ります。彼らは特定のタスクに対して、単純化されたリサーチ・ループ（検索→収集→要約）を実行し、コンテキストの分離を保証します 4。
    
- 統合／ライターエージェント: 全てのサブトピックについて収集されたリサーチ結果を受け取り、それらを序論、本文、結論を持つ、一貫性のある構造化された単一のレポートにまとめ上げる責任を負います 12。
    

- graph.pyでの実装:
    

- グラフは根本的に再設計されます。
    
- ノード: planner、run_parallel_research、synthesizer。
    
- plannerノードはサブタスクのリストを生成します。
    
- run_parallel_researchノードは「ディスパッチャー」として機能します。サブタスクのリストを受け取り、LangGraphのSendディレクティブを使用して、research_agentサブグラフの複数の並列呼び出しを生成します（各サブタスクに1つ） 2。
    
- synthesizerノードは、すべての並列リサーチブランチが完了した後にのみ呼び出されます。共有ステートから結果を集約し、最終レポートを生成します。
    

- 状態管理 (state.py): OverallStateのTypedDictを拡張し、この複雑性を管理します。research_plan: dict、completed_research: list[dict]、final_report: strなどの新しいフィールドが含まれます。
    

  

### 2.3. 表1: リサーチエージェントアーキテクチャの比較

  

この表は、ユーザーがニーズに合った適切なアーキテクチャを選択するのに役立つ、明確で一覧性の高い比較を提供します。

  

|   |   |   |   |
|---|---|---|---|
|特徴|ベースラインループ (Quickstart)|生成・批評ループ|スーパーバイザー・ワーカーモデル|
|コアコンセプト|単一エージェントによる反復的な検索と考察|生成されたドラフトに対する自己修正ループ|専門エージェントチームを統括する階層的オーケストレーション|
|複雑性|低|中|高|
|スケーラビリティ|低（逐次処理）|中（品質向上に焦点）|高（並列処理）|
|制御 vs. 自律性|高い制御、低い自律性|制御と自律性のバランス|スーパーバイザーによる高レベルの制御、ワーカーの自律性|
|コストへの影響|低|中|高（LLM呼び出し回数が増加するが、サブタスクに小型モデルを使用可能 14）|
|最適な用途|単純な事実確認、基本的な質問応答|高品質な要約、短いレポート生成|包括的なレポート、複雑なトピックの深掘り調査|

この比較表は、単なる概念の羅列ではなく、実践的な意思決定ツールとして機能します。例えば、「生成・批評ループ」は中程度の複雑性で高品質な出力を提供する一方、「スーパーバイザー・ワーカーモデル」は大規模なスケーラビリティを実現しますが、大幅なアーキテクチャ変更を必要とします 5。コストのような具体的な要素を明記することで、予算、納期、そして求められる能力に基づいた、情報に基づくエンジニアリング上の判断が可能になります。

---

## セクション3: エージェント専門化のための高度なプロンプトエンジニアリング

  

このセクションでは、エージェントの知能の「ソースコード」であるプロンプトを詳述します。マルチエージェントシステムにおいて、プロンプトは単なる指示書ではなく、エージェント間のAPI契約として機能します。プランナーのJSON出力は、スーパーバイザーがリサーチャーエージェントを呼び出すための形式的なAPIコールであり、リサーチャーからの構造化テキストは、統合エージェントへのAPIペイロードです。この視点は、プロンプトエンジニアリングを、API設計と同等の厳密さ、すなわちバージョニング、明確なスキーマ定義、そして堅牢なエラーハンドリングが求められる、中心的なソフトウェアエンジニアリングの規律へと昇華させます。

  

### 3.1. プランナーエージェント: 構造化出力の強制

  

- 目的: ユーザーのクエリを機械可読な計画に変換すること。最も重要な要件は、LLMに有効なJSONを出力させることです 15。
    
- プロンプト技術:
    

1. 明確な指示: プロンプトを明確なコマンドで開始します。「あなたはリサーチプランナーです。あなたのタスクは、詳細で構造化されたリサーチ計画をJSON形式で作成することです。JSONオブジェクト以外のテキストは一切出力しないでください。」 17。
    
2. スキーマ定義: プロンプト内に、キー、型、説明を含む正確なJSONスキーマを提供します。例：{"research_question": "...", "sub_topics": [{"topic_name": "...", "search_queries": ["...", "..."]}]} 16。
    
3. Few-Shot（少数例）学習: モデルの応答を方向付けるために、ユーザーのクエリとそれに対応する望ましいJSON出力の完全な例を1〜2個含めます 18。
    

- prompts.py用の完全なプロンプト例:  
    Python  
    PLANNER_PROMPT = """  
    You are an expert research planner. Your role is to transform a user's research question into a structured, actionable research plan in JSON format.  
    You must adhere strictly to the JSON schema provided. Do not output any text, explanation, or markdown formatting outside of the JSON object.  
      
    JSON Schema:  
    {{  
      "research_question": "The original, high-level research question from the user.",  
      "sub_topics":  
        }}  
      ]  
    }}  
      
    Example:  
    User Question: "What are the latest trends in renewable energy, focusing on solar and wind power, and their economic impact?"  
      
    Your JSON Output:  
    {{  
      "research_question": "What are the latest trends in renewable energy, focusing on solar and wind power, and their economic impact?",  
      "sub_topics":  
        }},  
        {{  
          "topic_name": "Innovations and Market Trends in Wind Power",  
          "search_queries": [  
            "floating offshore wind turbine technology advancements",  
            "next-generation large-scale wind turbine designs",  
            "bladeless wind turbine viability and performance",  
            "wind energy storage solutions and grid integration"  
          ]  
        }},  
        {{  
          "topic_name": "Economic Impact of Solar and Wind Energy Adoption",  
          "search_queries": [  
            "levelized cost of energy (LCOE) solar vs wind 2024",  
            "job creation in the renewable energy sector statistics",  
            "impact of renewable energy subsidies on national economies",  
            "investment trends in solar and wind power projects"  
          ]  
        }}  
      ]  
    }}  
      
    Now, generate the JSON output for the following user question.  
      
    User Question: "{user_question}"  
      
    Your JSON Output:  
    """  
      
    

  

### 3.2. リサーチャーエージェント: 焦点の絞られた情報収集

  

- 目的: 全体的なリサーチ目標に惑わされることなく、単一のサブトピックに焦点を当てた検索を実行すること。
    
- プロンプト技術:
    

- 役割演技（ロールプレイング）: 「あなたはリサーチアシスタントです。あなたの唯一のタスクは、以下のトピックに関する情報を検索し、要約することです：{sub_topic}。」 12。
    
- コンテキストのスコープ設定: プロンプトには、エージェントがより広範なリサーチ問題を考慮すべきではなく、提供されたサブトピックに検索と要約を限定すべきであることを明示的に記述します。これは、マルチエージェントアプローチのコンテキスト分離という利点を活用するための鍵です 4。
    

- prompts.py用の完全なプロンプト例:  
    Python  
    RESEARCHER_PROMPT = """  
    You are a highly skilled research assistant. Your sole task is to conduct a thorough web search on the provided topic and generate a concise, factual summary of your findings.  
      
    Your response must be a self-contained summary based ONLY on the information you find.  
    Do not consider any broader context or other topics. Focus exclusively on the topic provided below.  
    The summary should be well-organized, easy to read, and cover the key points of the topic.  
    List the URLs of the most relevant sources you used at the end of your summary.  
      
    Topic to Research: "{sub_topic}"  
      
    Begin your research and provide the summary.  
    """  
      
    

  

### 3.3. 統合エージェント: 一貫した物語の構築

  

- 目的: 複数のリサーチャーエージェントから得られた、潜在的に異なり、矛盾する可能性のある情報を、単一の構造化されたレポートに統合すること。
    
- プロンプト技術:
    

- 構造の提供: すべてのリサーチ結果の全文を、明確に区切られた形で提供します（例：「--- サブトピック1のリサーチ結果 ---... --- サブトピック2のリサーチ結果 ---...」）。
    
- 統合の指示: 中核となる指示は、「提供されたリサーチ結果に基づき、包括的なレポートを作成してください。レポートには序論、各サブトピックのセクション、そして結論となる要約を含める必要があります。リサーチで見つかった矛盾点があれば、それを認識し、言及してください。」とします 19。
    
- 引用の義務化: プロンプトには、行われたすべての主張に対して、セクション4で詳述するように、情報源を引用するという厳格な指示を含めます。
    

- prompts.py用の完全なプロンプト例:  
    Python  
    SYNTHESIZER_PROMPT = """  
    You are an expert report writer and analyst. Your task is to synthesize the provided research findings from multiple assistants into a single, high-quality, and comprehensive research report.  
      
    The report must be well-structured, with a clear introduction, a dedicated section for each sub-topic, and a final conclusion.  
    You must analyze all the provided information and create a coherent narrative. If you find conflicting information across different research findings, you must highlight these discrepancies and attempt to reconcile them or suggest reasons for the differences.  
      
    CRITICAL INSTRUCTION: You must cite your sources for every piece of information you include. At the end of each sentence or claim, append the citation marker in the format ``. The source IDs are provided within the research findings. A single sentence can have multiple citations if the information comes from multiple sources.  
      
    Here are the research findings for each sub-topic:  
    -----------------  
    {research_results}  
    -----------------  
      
    Based on the information above, write the full research report on the topic: "{research_question}"  
    """  
      
    

---

## セクション4: 堅牢な引用とグラウンディングの実装

  

信頼性の高いリサーチツールにとって、引用機能は不可欠です。ここでは、引用をシステムに統合するための明確で段階的なアルゴリズムを提示します 2。

  

### 4.1. 引用ワークフローのアルゴリズム

  

1. 取り込みとインデックス作成: web_searchステップでドキュメントを取得する際に、その内容とメタデータ（URL、タイトル）を保存し、一意の整数IDを割り当てます。
    
2. コンテキストのフォーマット: 取得したドキュメントを最終的な統合エージェントに渡す前に、フォーマットされたコンテキスト文字列を作成します。各ドキュメントの内容の前に、Source ID: \nContent:...のように一意のIDを付加します 22。
    
3. プロンプトによる指示: synthesizerエージェントのプロンプトには、「行うすべての主張について、文末に対応するSource ID: [id]を付加して情報源を引用しなければならない」という、明確かつ交渉の余地のない指示を含める必要があります 24。
    
4. 出力の強制: LLMのツール呼び出し機能または構造化出力機能を利用します。CitedAnswer(answer: str, citations: List[int])のようなPydanticスキーマを定義し、.with_structured_output(CitedAnswer)を使用してモデル呼び出しにバインドします 23。これにより、モデルはテキストを生成するだけでなく、使用したソースIDのクリーンなリストも生成せざるを得なくなります。
    
5. 後処理: 最終的なアプリケーションは、このcitationsリストを使用して、最初のステップで保存された元のソースドキュメントにリンクバックすることができます。
    

  

### 4.2. graph.pyとutils.pyにおけるコード実装

  

ここでは、具体的なPythonコードスニペットを提供します。

- utils.py: コンテキスト文字列を作成するための新しい関数format_docs_with_idを定義します。  
    Python  
    from typing import List  
    # langchain_core.documents.Document を想定  
    from langchain_core.documents import Document  
      
    def format_docs_with_id(docs: List) -> str:  
        """  
        ドキュメントのリストを、各ドキュメントに一意のIDを付けて  
        フォーマットされた単一の文字列に変換します。  
        """  
        formatted_strings =  
        for i, doc in enumerate(docs):  
            # doc.metadataに'source'や'title'が含まれていることを想定  
            source_info = doc.metadata.get('source', 'Unknown Source')  
            formatted_string = f"Source ID: [{i}]\nURL: {source_info}\nContent: {doc.page_content}"  
            formatted_strings.append(formatted_string)  
        return "\n\n---\n\n".join(formatted_strings)  
      
    
- graph.py内のsynthesizerノード: Pydanticスキーマ定義と.with_structured_output()モデル呼び出しを示すようにsynthesizerノード関数を変更します。  
    Python  
    from pydantic import BaseModel, Field  
    from typing import List  
      
    # Pydanticモデルを定義して、引用付きの回答を構造化する  
    class CitedAnswer(BaseModel):  
        """指定された情報源のみに基づいてユーザーの質問に回答し、使用した情報源を引用する。"""  
        answer: str = Field(  
          ...,  
            description="ユーザーの質問に対する回答。提供された情報源のみに基づく。",  
        )  
        citations: List[int] = Field(  
          ...,  
            description="回答を正当化する特定の情報源の整数ID。",  
        )  
      
    #... synthesizer ノード関数内...  
    # llm は ChatGoogleGenerativeAI などのインスタンス  
    structured_llm = llm.with_structured_output(CitedAnswer)  
      
    # research_results はフォーマットされたドキュメント文字列  
    # research_question はユーザーの元の質問  
    prompt = SYNTHESIZER_PROMPT.format(  
        research_results=research_results,  
        research_question=research_question  
    )  
      
    response = structured_llm.invoke(prompt)  
      
    # response.answer と response.citations を後続の処理で使用する  
    final_report_text = response.answer  
    # 引用情報を最終出力に含める  
    #...  
      
    

---

## セクション5: 制御と知識の永続性の強化

  

自律的なエージェントは強力ですが、その能力を最大限に引き出し、信頼性を確保するためには、人間による監督と、得られた知識を将来にわたって活用するためのメカニズムが必要です。

  

### 5.1. 品質保証のためのヒューマンインザループ（HITL）

  

- 概念: エージェントは自律的に動作できますが、重要なタスクは人間の監督から恩恵を受けます。LangGraphに組み込まれたチェックポイントシステムは、グラフの実行を一時停止し、外部からの入力を待機することを可能にします 21。
    
- 実装: 2つの重要なチェックポイントを追加する方法を示します。
    

1. 計画の承認: plannerノードの後に、human_approvalノードを挿入します。このノードはLangGraphのinterrupt()関数を使用して実行を一時停止し、生成されたリサーチ計画をAPI経由でユーザーに提示します。ユーザーはリサーチが開始される前に計画を承認または編集できます 21。
    
2. 最終ドラフトのレビュー: final_reportがENDノードに送られる前に、別のhuman_approvalチェックポイントを挿入し、統合されたレポートの最終的な人間によるレビューを可能にします。
    

- interruptを定義する方法と、アプリケーションがユーザーのフィードバックを受けてグラフの実行を再開する方法を示すコード例が提供されます。
    

  

### 5.2. 高度な技術：動的なナレッジグラフの構築

  

- 概念: これは、エージェントを単一タスクのツールから、継続的な知識構築システムへと変革する、先進的な機能強化です。情報収集後、構造化データ（エンティティとリレーションシップ）を抽出し、ナレッジグラフ（KG）を構築するノードを追加できます 26。
    
- ワークフロー:
    

1. 並列リサーチフェーズの後、統合の前にbuild_knowledge_graphノードを追加します。
    
2. このノードは、特定のプロンプトを持つLLMを使用して、収集されたテキストを解析し、三つ組（例：(エンティティ1, 関係, エンティティ2)）を抽出します 27。
    
3. これらの三つ組は、Neo4jのようなグラフデータベースに追加されます 26。
    

- 利点と意義:
    

- 知識の永続性: エージェントの発見はセッション終了後も失われません。KGは長期的な記憶として機能します 29。
    
- 検索能力の向上: 将来のリサーチタスクにおいて、エージェントはウェブを検索する前にKGに既存の知識を問い合わせることができ、より迅速で正確な結果につながります（GraphRAG） 31。
    

- このセクションでは、概念的な概要と、LLMGraphTransformerのような実装リソースへのポインタを提供します 27。
    

---

## セクション6: 実践的な実装ロードマップ

  

この最終セクションでは、すべての概念を統合し、gemini-fullstack-langgraph-quickstartリポジトリをリファクタリングするための明確で実行可能な計画を提供します。

  

### 6.1. prompts.pyのリファクタリング

  

Planner、Researcher、Synthesizer、Criticの各役割に対応する、専門的に作成された明確なプロンプトを含む、prompts.pyファイルの完全な最終版を提供します。

  

Python

  
  

# backend/src/agent/prompts.py (最終版)  
  
PLANNER_PROMPT = """  
You are an expert research planner. Your role is to transform a user's research question into a structured, actionable research plan in JSON format.  
You must adhere strictly to the JSON schema provided. Do not output any text, explanation, or markdown formatting outside of the JSON object.  
  
JSON Schema:  
{{  
  "research_question": "The original, high-level research question from the user.",  
  "sub_topics":  
    }}  
  ]  
}}  
  
Example:  
User Question: "What are the latest trends in renewable energy, focusing on solar and wind power, and their economic impact?"  
  
Your JSON Output:  
{{  
  "research_question": "What are the latest trends in renewable energy, focusing on solar and wind power, and their economic impact?",  
  "sub_topics":}},  
    {{"topic_name": "Innovations and Market Trends in Wind Power", "search_queries": ["floating offshore wind turbine technology advancements", "next-generation large-scale wind turbine designs"]}},  
    {{"topic_name": "Economic Impact of Solar and Wind Energy Adoption", "search_queries": ["levelized cost of energy (LCOE) solar vs wind 2024", "job creation in the renewable energy sector statistics"]}}  
  ]  
}}  
  
Now, generate the JSON output for the following user question.  
  
User Question: "{user_question}"  
  
Your JSON Output:  
"""  
  
RESEARCHER_PROMPT = """  
You are a highly skilled research assistant. Your sole task is to conduct a thorough web search on the provided topic and generate a concise, factual summary of your findings.  
Your response must be a self-contained summary based ONLY on the information you find.  
Do not consider any broader context or other topics. Focus exclusively on the topic provided below.  
The summary should be well-organized, easy to read, and cover the key points of the topic.  
At the end of your summary, provide a list of the URLs of the most relevant sources you used, formatted as:  
SOURCES:  
-  
-  
  
Topic to Research: "{sub_topic}"  
  
Begin your research and provide the summary.  
"""  
  
SYNTHESIZER_PROMPT = """  
You are an expert report writer and analyst. Your task is to synthesize the provided research findings from multiple assistants into a single, high-quality, and comprehensive research report.  
The report must be well-structured, with a clear introduction, a dedicated section for each sub-topic, and a final conclusion.  
You must analyze all the provided information and create a coherent narrative. If you find conflicting information across different research findings, you must highlight these discrepancies and attempt to reconcile them or suggest reasons for the differences.  
  
CRITICAL INSTRUCTION: You must cite your sources for every piece of information you include. At the end of each sentence or claim, append the citation marker in the format ``. The source IDs are provided within the research findings. A single sentence can have multiple citations if the information comes from multiple sources.  
  
Here are the research findings for each sub-topic:  
-----------------  
{research_results}  
-----------------  
  
Based on the information above, write the full research report on the topic: "{research_question}"  
"""  
  
CRITIQUE_PROMPT = """  
You are a meticulous and critical editor. Your task is to review the provided research report draft and evaluate it based on the following criteria:  
1.  **Accuracy**: Are the claims factually correct and supported by the provided research?  
2.  **Completeness**: Does the report adequately address all aspects of the original research question? Are there any obvious gaps?  
3.  **Clarity**: Is the report well-written, easy to understand, and logically structured?  
4.  **Citations**: Are all claims properly cited according to the required format ``?  
  
Provide your feedback in a structured format. First, give an overall assessment. Then, provide specific, actionable suggestions for improvement.  
If the report is excellent and requires no changes, state "The report is satisfactory."  
  
Report Draft to Review:  
-----------------  
{draft_report}  
-----------------  
  
Begin your critique.  
"""  
  

  

### 6.2. graph.pyのリファクタリング

  

StateGraphを再構築するための段階的なガイドを提供します。これには、新しいノード（planner, run_parallel_research, synthesizer, critique_report, human_approval）と、批評ループや並列ディスパッチメカニズムを含む新しいエッジの最終的なコードが含まれます。

  

### 6.3. 状態定義の変更

  

拡張されたOverallStateのTypedDictの最終版を提供し、各新しいフィールドの目的を説明します。

  

Python

  
  

# backend/src/agent/state.py (最終版の例)  
from typing import TypedDict, Annotated, List, Dict, Any  
from langgraph.graph.message import add_messages  
import operator  
  
class SubTopicResearch(TypedDict):  
    topic_name: str  
    summary: str  
    sources: List[str]  
  
class OverallState(TypedDict):  
    messages: Annotated[list, add_messages]  
    research_question: str  
    research_plan: Dict[str, Any]  
    # 並列リサーチの結果を格納  
    research_results: Annotated, operator.add]  
    # 統合されたレポートのドラフト  
    draft_report: str  
    # 批評家からのフィードバック  
    critique: str  
    # 最終レポート  
    final_report: str  
    # リビジョン回数の追跡  
    revisions_count: int  
  

  

### 6.4. 最終アーキテクチャ図

  

スーパーバイザー・ワーカーグラフ全体を視覚化するMermaidダイアグラムを提供します。これにより、並列ブランチやフィードバックループを含む、すべてのノード間の制御とデータの流れが示され、完成したシステムの明確なメンタルモデルが提供されます 34。

  

コード スニペット

  
  

graph TD  
    A --> B(planner);  
    B --> C{plan_approval_hitl};  
    C -- Approved --> D(run_parallel_research);  
    C -- Edited --> B;  
    D -- for each sub_topic --> E[research_agent_subgraph];  
    E --> F(aggregate_results);  
    F --> G(synthesizer);  
    G --> H(critique_report);  
    H --> I{should_revise};  
    I -- Revise --> G;  
    I -- Satisfactory --> J{final_review_hitl};  
    J -- Approved --> K;  
    J -- Edited --> G;  
  

#### 引用文献

1. LangGraph 101: Let's Build A Deep Research Agent | Towards Data Science, 9月 14, 2025にアクセス、 [https://towardsdatascience.com/langgraph-101-lets-build-a-deep-research-agent/](https://towardsdatascience.com/langgraph-101-lets-build-a-deep-research-agent/)
    
2. Automating Web Research - LangChain Blog, 9月 14, 2025にアクセス、 [https://blog.langchain.com/automating-web-research/](https://blog.langchain.com/automating-web-research/)
    
3. Open Deep Research - LangChain Blog, 9月 14, 2025にアクセス、 [https://blog.langchain.com/open-deep-research/](https://blog.langchain.com/open-deep-research/)
    
4. LangGraph Deep Research: A Tale of Two Architectures - DataHub, 9月 14, 2025にアクセス、 [https://datahub.io/@donbr/langgraph-unleashed/langgraph_deep_research](https://datahub.io/@donbr/langgraph-unleashed/langgraph_deep_research)
    
5. Building a Deep Research Agent with LangGraph - Sid Bharath, 9月 14, 2025にアクセス、 [https://www.siddharthbharath.com/build-deep-research-agent-langgraph/](https://www.siddharthbharath.com/build-deep-research-agent-langgraph/)
    
6. LangGraph — Build Self-Improving Agents | by Shuvrajyoti Debroy ..., 9月 14, 2025にアクセス、 [https://medium.com/@shuv.sdr/langgraph-build-self-improving-agents-8ffefb52d146](https://medium.com/@shuv.sdr/langgraph-build-self-improving-agents-8ffefb52d146)
    
7. Reflection Agents - LangChain Blog, 9月 14, 2025にアクセス、 [https://blog.langchain.com/reflection-agents/](https://blog.langchain.com/reflection-agents/)
    
8. A Deep Dive into LangGraph for Self-Correcting AI Agents | ActiveWizards, 9月 14, 2025にアクセス、 [https://activewizards.com/blog/a-deep-dive-into-langgraph-for-self-correcting-ai-agents](https://activewizards.com/blog/a-deep-dive-into-langgraph-for-self-correcting-ai-agents)
    
9. Agentic AI With LangGraph: Building a Writer–Critic Loop (AAIDC-Week5-Lesson-2c), 9月 14, 2025にアクセス、 [https://app.readytensor.ai/publications/agentic-ai-with-langgraph-building-a-writercritic-loop-aaidc-week5-lesson-2c-zvrcImvr8AF4](https://app.readytensor.ai/publications/agentic-ai-with-langgraph-building-a-writercritic-loop-aaidc-week5-lesson-2c-zvrcImvr8AF4)
    
10. LangGraph Multi-Agent Systems - Overview, 9月 14, 2025にアクセス、 [https://langchain-ai.github.io/langgraph/concepts/multi_agent/](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
    
11. Building Multi-Agent Systems with LangGraph | by Clearwater Analytics Engineering, 9月 14, 2025にアクセス、 [https://medium.com/cwan-engineering/building-multi-agent-systems-with-langgraph-04f90f312b8e](https://medium.com/cwan-engineering/building-multi-agent-systems-with-langgraph-04f90f312b8e)
    
12. Learn to Generate Reports with LangGraph and AI | datos.gob.es, 9月 14, 2025にアクセス、 [https://datos.gob.es/en/conocimiento/learn-generate-reports-langgraph-and-ai](https://datos.gob.es/en/conocimiento/learn-generate-reports-langgraph-and-ai)
    
13. langchain-ai/open_deep_research - GitHub, 9月 14, 2025にアクセス、 [https://github.com/langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research)
    
14. Prompt Engineering for AI Agents - PromptHub, 9月 14, 2025にアクセス、 [https://www.prompthub.us/blog/prompt-engineering-for-ai-agents](https://www.prompthub.us/blog/prompt-engineering-for-ai-agents)
    
15. JSON Prompt: The Ultimate Guide to Perfect AI Outputs - MPG ONE, 9月 14, 2025にアクセス、 [https://mpgone.com/json-prompt-guide/](https://mpgone.com/json-prompt-guide/)
    
16. How to Output JSON? Function calling or prompting? - API - OpenAI Developer Community, 9月 14, 2025にアクセス、 [https://community.openai.com/t/how-to-output-json-function-calling-or-prompting/409700](https://community.openai.com/t/how-to-output-json-function-calling-or-prompting/409700)
    
17. Prompt engineering techniques - Azure OpenAI | Microsoft Learn, 9月 14, 2025にアクセス、 [https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/prompt-engineering](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/prompt-engineering)
    
18. How Multi-Agent LLMs Are Revolutionizing Prompt Engineering by Writing Their Own Prompts | by Gary A. Fowler | Aug, 2025, 9月 14, 2025にアクセス、 [https://gafowler.medium.com/how-multi-agent-llms-are-revolutionizing-prompt-engineering-by-writing-their-own-prompts-c1a6f9410f8d](https://gafowler.medium.com/how-multi-agent-llms-are-revolutionizing-prompt-engineering-by-writing-their-own-prompts-c1a6f9410f8d)
    
19. Advanced Prompt Engineering for AI Agents: Building Intelligent Workflows - PromptAgent, 9月 14, 2025にアクセス、 [https://promptagent.uk/advanced-prompt-engineering-for-ai-agents-building-intelligent-workflows/](https://promptagent.uk/advanced-prompt-engineering-for-ai-agents-building-intelligent-workflows/)
    
20. LangGraph 201: Adding Human Oversight to Your Deep Research Agent, 9月 14, 2025にアクセス、 [https://towardsdatascience.com/langgraph-201-adding-human-oversight-to-your-deep-research-agent/](https://towardsdatascience.com/langgraph-201-adding-human-oversight-to-your-deep-research-agent/)
    
21. How to return citations - LangChain.js, 9月 14, 2025にアクセス、 [https://js.langchain.com/docs/how_to/qa_citations/](https://js.langchain.com/docs/how_to/qa_citations/)
    
22. How to get a RAG application to add citations | 🦜️ LangChain, 9月 14, 2025にアクセス、 [https://python.langchain.com/docs/how_to/qa_citations/](https://python.langchain.com/docs/how_to/qa_citations/)
    
23. How to add 'source citation' for Langchain's Question-Answering based on PDFs? - Reddit, 9月 14, 2025にアクセス、 [https://www.reddit.com/r/LangChain/comments/157833e/how_to_add_source_citation_for_langchains/](https://www.reddit.com/r/LangChain/comments/157833e/how_to_add_source_citation_for_langchains/)
    
24. LangGraph - LangChain, 9月 14, 2025にアクセス、 [https://www.langchain.com/langgraph](https://www.langchain.com/langgraph)
    
25. How to construct knowledge graphs - LangChain.js, 9月 14, 2025にアクセス、 [https://js.langchain.com/docs/how_to/graph_constructing/](https://js.langchain.com/docs/how_to/graph_constructing/)
    
26. How to construct knowledge graphs | 🦜️ LangChain, 9月 14, 2025にアクセス、 [https://python.langchain.com/docs/how_to/graph_constructing/](https://python.langchain.com/docs/how_to/graph_constructing/)
    
27. getzep/graphiti: Build Real-Time Knowledge Graphs for AI Agents - GitHub, 9月 14, 2025にアクセス、 [https://github.com/getzep/graphiti](https://github.com/getzep/graphiti)
    
28. What is LangGraph? - IBM, 9月 14, 2025にアクセス、 [https://www.ibm.com/think/topics/langgraph](https://www.ibm.com/think/topics/langgraph)
    
29. LangGraph Tutorial: Building LLM Agents with LangChain's Agent Framework - Zep, 9月 14, 2025にアクセス、 [https://www.getzep.com/ai-agents/langgraph-tutorial/](https://www.getzep.com/ai-agents/langgraph-tutorial/)
    
30. Improved Knowledge Graph Creation with LangChain and LlamaIndex - Memgraph, 9月 14, 2025にアクセス、 [https://memgraph.com/blog/improved-knowledge-graph-creation-langchain-llamaindex](https://memgraph.com/blog/improved-knowledge-graph-creation-langchain-llamaindex)
    
31. How to incorporate a knowledge graph in RAG : r/LangChain - Reddit, 9月 14, 2025にアクセス、 [https://www.reddit.com/r/LangChain/comments/1duz8qc/how_to_incorporate_a_knowledge_graph_in_rag/](https://www.reddit.com/r/LangChain/comments/1duz8qc/how_to_incorporate_a_knowledge_graph_in_rag/)
    
32. Building Knowledge Graphs with LLM Graph Transformer | by Tomaz Bratanic - Medium, 9月 14, 2025にアクセス、 [https://medium.com/data-science/building-knowledge-graphs-with-llm-graph-transformer-a91045c49b59](https://medium.com/data-science/building-knowledge-graphs-with-llm-graph-transformer-a91045c49b59)
    
33. Build a Multi-Agent System with LangGraph and Mistral on AWS | Artificial Intelligence, 9月 14, 2025にアクセス、 [https://aws.amazon.com/blogs/machine-learning/build-a-multi-agent-system-with-langgraph-and-mistral-on-aws/](https://aws.amazon.com/blogs/machine-learning/build-a-multi-agent-system-with-langgraph-and-mistral-on-aws/)
    
