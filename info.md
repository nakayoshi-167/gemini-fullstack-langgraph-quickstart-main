## Deep Research の仕組み

### 全体アーキテクチャ

今回の例では Claude 3.7 Sonnet をベースに、Web 検索やプランニングなどの機能を持つツールを組み合わせています。

```
ユーザーの質問 → パラメータ分析 → ツール実行 → 調査レポート出力
```

1. **LLM**: Claude 3.7 Sonnet など
2. **ツール群**: Web 検索、調査計画、振り返り分析などの機能
3. **システムプロンプト**: エージェントの振る舞いを定義する詳細な指示

### 調査プロセス

Deep Research の調査プロセスは大きく「計画・構造化」と「調査」の 2 つのフェーズから構成されています。

#### 1\. 計画と構造化フェーズ

1. **トピック分析**
	- ユーザーの質問を分析し、トピックの概要を把握
	- 質問の複雑さに応じて、適切な調査パラメータを決定
2. **調査計画の作成**
	- `planResearchTool`を使用して調査計画を立案
	- OpenAI の o3-mini モデルを利用して計画を策定
	- レポートの構造（イントロダクション、各セクション、結論）を決定

#### 2\. 調査フェーズ

1. **検索クエリの生成**
	- 各セクションに対して複数の検索クエリを作成
	- 検索クエリには日付や「最新」などの時間的キーワードを含める
2. **ウェブ検索の実行**
	- `webSearchTool`（Tavily 検索 API）を使用して情報収集
	- 各クエリに対して検索を実行し、結果を取得
3. **情報の処理と分析**
	- 検索結果から重要な情報を抽出・整理
	- 情報の信頼性と最新性を評価
	- 情報の日付を確認し記録
4. **振り返りと改善**
	- `reflectOnResultsTool`を使用して検索結果を振り返り
	- 次の検索クエリを改善するための分析
	- 情報のギャップや不足している視点を特定
5. **反復的な検索**
	- 複数回の検索反復を通じて情報を充実
	- 改善されたクエリで再検索を行う
6. **最終レポートの作成**
	- 収集した情報を統合し、構造化されたレポートを作成
	- マークダウン形式で出力

### パラメータ分析

調査の質と深さを決定する重要な要素として、2 つの主要パラメータがあります。

1. **searchQueriesPerSection**: 各セクションで実行する検索クエリの数（1〜5）
2. **searchIterations**: 各クエリに対して実行する検索反復の回数（1〜5）

これらのパラメータは、ユーザーの質問内容に基づいて自動的に最適化されます。モデルが質問の複雑さや範囲を分析し、適切なパラメータを決定します。

```
// パラメータ生成の一部
const { object: parameters } = await generateObject({
  model: anthropic("claude-3-5-haiku-latest"),
  schema: z.object({
    searchQueriesPerSection: z
      .number()
      .min(1)
      .max(5)
      .describe("各セクションで実行する検索クエリの数"),
    searchIterations: z
      .number()
      .min(1)
      .max(5)
      .describe("各クエリに対して実行する検索反復の回数"),
    reasoning: z.string().describe("パラメータ選択の理由"),
  }),
  prompt: \`以下のユーザーの質問を分析し、適切な研究パラメータを決定してください：...\`,
});
```

この分析により、簡単な質問に対しては効率的な調査が、複雑な質問に対しては詳細で広範な調査が実行されます。

## 実装の詳細

### 使用しているツール

Deep Research は、以下の 3 つの主要ツールを使用しています。

1. **webSearchTool**
	- 機能: Web 検索を実行して情報を収集
	- 実装: Tavily API を使用して検索を実行
	- パラメータ: 検索クエリ、セクション（オプション）、反復回数（オプション）

```
export const webSearchTool = tool({
  description: "ウェブ検索を実行して情報を収集する",
  parameters: z.object({
    query: z.string().describe("検索クエリ"),
    section: z
      .string()
      .optional()
      .describe("この検索が関連するレポートのセクション（オプション）"),
    iteration: z
      .number()
      .optional()
      .describe("現在の検索反復回数（オプション）"),
  }),
  execute: async ({ query, section, iteration }) => {
    console.log(
      "ウェブ検索実行中",
      query,
      section ? \`セクション: ${section}\` : "",
      iteration ? \`反復: ${iteration}\` : ""
    );

    try {
      const res = await tavily.search(query);

      console.log("検索結果:", res);

      // 検索結果を整形して返す
      const formattedResults = {
        results:
          res.results.map((result) => ({
            title: result.title,
            url: result.url,
            content: result.content,
            score: result.score,
          })) || [],
        search_metadata: {
          query: query,
          section: section,
          iteration: iteration,
          timestamp: new Date().toISOString(),
        },
      };

      console.log("検索結果取得完了", formattedResults.results.length, "件");

      return formattedResults;
    } catch (error) {
      console.error("検索エラー:", error);
      return {
        error: "検索実行中にエラーが発生しました",
        details: error instanceof Error ? error.message : String(error),
      };
    }
  },
});
```

2. **planResearchTool**
	- 機能: 調査計画を立てる
	- 実装: OpenAI o3-mini モデルを使用して調査計画を生成
	- 返り値: 調査目的、セクション構成、構造（イントロダクション・結論）

```
export const planResearchTool = tool({
  description: "ユーザーの質問に基づいて包括的な調査計画を立てる",
  parameters: z.object({
    query: z.string().describe("ユーザーの元の質問やクエリ"),
    plannerModel: z.string().describe("使用するプランナーモデル（例：o3 等）"),
  }),
  execute: async ({ query, plannerModel, companyName, depth, breadth }) => {
    console.log(\`調査計画を実行中, プランナーモデル: ${plannerModel}\`);

    // 企業調査かどうかに応じてプロンプトを選択
    const prompt = PLANNER_PROMPT.replace("{query}", query);

    const sectionsSchema = z.object({
      title: z.string().describe("セクションのタイトル"),
      focus: z.string().describe("このセクションの焦点"),
      key_questions: z
        .array(z.string())
        .describe("このセクションで探求すべき主要な質問"),
    });

    const { object } = await generateObject({
      model: openai("o3-mini"),
      schema: z.object({
        research_plan: z.object({
          purpose: z.string().describe("調査の目的と範囲"),
          sections: z.array(sectionsSchema),
          structure: z.object({
            introduction: z.string().describe("イントロダクションの概要"),
            conclusion: z.string().describe("結論の概要"),
          }),
        }),
        meta_analysis: z.string().describe("計画に関する分析と推奨事項"),
      }),
      prompt: prompt,
      providerOptions: {
        openai: {
          reasoningEffort: "low",
        },
      },
    });

    console.log("調査計画の結果:", object.meta_analysis);

    const result = {
      research_plan: object.research_plan,
      meta_analysis: object.meta_analysis,
    };

    return {
      ...result,
      planner_model: plannerModel,
    };
  },
});
```

3. **reflectOnResultsTool**
	- 機能: 検索結果を分析し、次の検索を改善するための洞察を提供
	- 実装: OpenAI モデルを使用して検索結果の分析
	- パラメータ: 検索クエリ、検索結果、反復回数、総反復回数

```
export const reflectOnResultsTool = tool({
  description:
    "検索結果を分析し、次の検索をより効果的にするための洞察を提供する",
  parameters: z.object({
    query: z.string().describe("検索に使用した元のクエリ"),
    results: z.string().describe("検索から得られた結果"),
    iteration: z.number().describe("現在の検索反復回数"),
    totalIterations: z.number().describe("計画された総検索反復回数"),
  }),
  execute: async ({ query, results, iteration, totalIterations }) => {
    console.log(
      \`検索結果の振り返りを実行中, 反復: ${iteration}/${totalIterations}\`
    );

    const prompt = REFLECTION_PROMPT.replace("{query}", query).replace(
      "{results}",
      results
    );

    const keyInsightsSchema = z.object({
      insight: z.string().describe("検索結果から得られた重要な洞察"),
      confidence: z
        .number()
        .min(1)
        .max(10)
        .describe("この洞察の信頼度（1-10）"),
      source_indication: z.string().describe("この洞察の出所に関する手がかり"),
    });

    const improvedQueriesSchema = z.object({
      query: z.string().describe("改善された検索クエリ"),
      rationale: z.string().describe("このクエリを提案する理由"),
    });

    const { object } = await generateObject({
      model: openai("gpt-4o"),
      schema: z.object({
        key_insights: z.array(keyInsightsSchema),
        information_gaps: z
          .array(z.string())
          .describe("特定された情報のギャップや不足している視点"),
        contradictions: z
          .array(z.string())
          .describe("検索結果内の矛盾する情報や検証が必要な主張"),
        improved_queries: z.array(improvedQueriesSchema),
        summary: z
          .string()
          .describe("振り返りの要約と次のステップへの推奨事項"),
      }),
      prompt: prompt,
    });

    console.log("振り返りの結果:", object.summary);

    const result = {
      key_insights: object.key_insights,
      information_gaps: object.information_gaps,
      contradictions: object.contradictions,
      improved_queries: object.improved_queries,
      summary: object.summary,
      current_iteration: iteration,
      total_iterations: totalIterations,
    };

    return result;
  },
});
```

### コアロジック

Deep Research のコア実装は、以下のようになっています。

```
// ユーザーの質問から研究パラメータを生成
const { searchQueriesPerSection, searchIterations } =
  await generateResearchParameters(
    messages[messages.length - 1].content as string
  );

// 最大ステップ数を計算
const estimatedSections = 5;
const maxSteps =
  10 + estimatedSections * searchQueriesPerSection * searchIterations * 2;

// パラメータをシステムプロンプトに反映
const generatedSystemPrompt = DEEP_RESEARCH_SYSTEM_PROMPT.replace(
  "[PLANNER_MODEL]",
  "o3"
)
  .replace("[SEARCH_QUERIES_PER_SECTION]", String(searchQueriesPerSection))
  .replace("[SEARCH_API]", "Tavily")
  .replace("[SEARCH_ITERATIONS]", String(searchIterations));

// LLMとツールを使用してストリーミング応答を生成
const result = streamText({
  model: anthropic(modelName),
  system: generatedSystemPrompt,
  messages: messages,
  maxSteps: maxSteps,
  tools: {
    webSearch: webSearchTool,
    planResearch: planResearchTool,
    reflectOnResults: reflectOnResultsTool,
  },
});
```

### システムプロンプト

```
export const DEEP_RESEARCH_SYSTEM_PROMPT = \`あなたは高度な調査エージェントです。ユーザーの質問に対して深く、包括的な調査を行います。

## 調査プロセス
あなたは以下の2つの主要フェーズに従って調査を行います：

### 1. 計画と構造化（Planning / Structure）
1. まず、getCurrentDateツールを使用して現在の日付を取得します。
   - 取得した日付を使用して、情報の鮮度を評価します
   - レポートに日付を明記し、いつの時点の情報かを明確にします
2. ユーザーの質問を分析し、トピックの概要を把握します。
3. 指定されたプランナーモデル（[PLANNER_MODEL]）を使用して調査計画を立てます。
4. 以下の構造に基づいて調査レポートの概要を作成します：
   - イントロダクション（調査の目的、背景、調査日を含む）
   - セクション1
   - セクション2
   - ...
   - 結論
5. 計画を確認し、必要に応じて調整します。

### 2. 調査（Research）
1. 各セクションについて、[SEARCH_QUERIES_PER_SECTION]個の検索クエリを作成します。
   - 検索クエリに日付や「最新」「recent」などの時間的キーワードを含めて、最新の情報を優先的に取得します
2. 各クエリに対して[SEARCH_API]を使用して情報を収集します。
   - webSearchツールを使用してウェブ検索を実行します
   - 検索結果の日付を確認し、古い情報は注意して扱います
3. 検索結果を処理し、以下を行います：
   - 重要な情報を抽出し、整理します
   - 情報の信頼性と最新性を評価します
   - 情報の日付を確認し、いつの情報かを明記します
4. 各検索結果について振り返り（Reflection）を行い、次の検索クエリを改善します。
5. 合計[SEARCH_ITERATIONS]回の検索反復を行います。
6. 収集した情報を統合し、構造化されたレポートをセクションごとに作成します。

## レポート作成のガイドライン
1. 計画した構造に従って情報を整理します。
2. 見出し (H1, H2, H3) の前後には改行を入れ、マークダウン形式で正しく表示します。
3. 重要な事実や主張を述べる際は、必ず対応する情報源のURLをマークダウンリンクとして文中に埋め込みます。
   - 例: 「[研究によると](https://example.com)、この方法は効果的です」
4. 同じ情報源から複数の事実を引用する場合でも、それぞれの事実に対して適切にリンクを付けます。
5. リンクのテキストは文脈に自然に溶け込むようにし、URLそのものは表示しないようにします。
6. 主要な発見事項、結論、および参考文献を含めます。
7. 情報の日付を明記し、特に最新の情報（過去3ヶ月以内）は強調します。
8. レポートの冒頭に調査日（getCurrentDateで取得した日付）を明記します。

## セクション出力形式
各セクションは以下の形式で出力してください：

# [セクションタイトル]

[セクションの内容：事実、分析、洞察など。情報源へのリンクを含める。情報の日付を明記する]

## 主要な発見

- [発見1]
- [発見2]
- [発見3]

## 情報源

- [情報源1へのリンク] (日付: YYYY-MM-DD)
- [情報源2へのリンク] (日付: YYYY-MM-DD)
- [情報源3へのリンク] (日付: YYYY-MM-DD)

## ツールの使用方法
- getCurrentDate: 現在の日付を取得します
- webSearch: ウェブ検索を実行して情報を収集します
- planResearch: 調査計画を立てます
- reflectOnResults: 検索結果を振り返り、次のクエリを改善します

常に批判的思考を用い、情報の信頼性を評価してください。複数の情報源を比較し、バランスの取れた見解を提供してください。\`;

// プランナーツール用のプロンプト
export const PLANNER_PROMPT = \`あなたは調査計画の専門家です。ユーザーの質問に基づいて、包括的な調査計画を立ててください。

以下の質問について調査計画を立ててください：
"{query}"

計画には以下を含めてください：
1. 調査の目的と範囲
2. 主要なセクション（3〜5個）とそれぞれの焦点
3. 各セクションで探求すべき主要な質問や側面
4. 調査全体の構造（イントロダクション、本文セクション、結論）

計画は論理的で体系的であり、質問のすべての重要な側面をカバーするようにしてください。\`;

// 振り返りツール用のプロンプト
export const REFLECTION_PROMPT = \`あなたは検索結果の分析と振り返りの専門家です。以下の検索結果を分析し、次の検索をより効果的にするための洞察を提供してください。

元の検索クエリ：
"{query}"

検索結果：
"{results}"

以下について分析してください：
1. 得られた主要な情報と洞察
2. 情報のギャップや不足している視点
3. 矛盾する情報や検証が必要な主張
4. 次の検索でより良い結果を得るための改善されたクエリ案

あなたの分析は、調査プロセスを改善し、より包括的で正確な情報を収集するのに役立ちます。\`;
```

### 開発のステップアップガイド

初めてのエージェント開発として Deep Research を実装する場合、以下のようなステップがおすすめです。

1. **ミニマム実装から始める**：最初は Web 検索とレポート生成だけのシンプルバージョンから
2. **徐々に機能を追加する**：reflectOnResults や planResearch などのツールを段階的に追加
3. **パラメータ最適化を試みる**：検索クエリ数や反復回数の自動調整機能を追加
4. **UI を整備する**：ユーザーが使いやすいインターフェースを設計

すでにプログラミングの経験がある方なら、週末ハッカソン 1 回分程度の時間で基本的な実装ができるでしょう。ぜひチャレンジしてみてください！