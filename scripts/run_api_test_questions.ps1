param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$OutputDir = "api_test_outputs"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$questions = @(
    @{
        Id = "assignment_1_precise_fact_retrieval"
        Type = "Assignment - precise fact retrieval"
        Question = "Find an article that reframes marketing as a conversation with readers, aimed at writers who find self-promotion uncomfortable. Provide the title and author."
    },
    @{
        Id = "assignment_2_multi_result_listing"
        Type = "Assignment - multi-result topic listing"
        Question = "List exactly 3 articles about education. Return only the titles."
    },
    @{
        Id = "assignment_3_key_idea_summary"
        Type = "Assignment - key idea summary extraction"
        Question = "Find an article that argues past pandemics such as the bubonic plague can spur innovation and recovery, and summarise its central argument."
    },
    @{
        Id = "assignment_4_recommendation"
        Type = "Assignment - recommendation with evidence"
        Question = "I want practical, beginner-friendly advice on building habits that actually stick. Which article would you recommend, and why?"
    },
    @{
        Id = "extra_1_health_listing"
        Type = "Extra - multi-result listing"
        Question = "List exactly 3 articles about health. Return only the titles."
    },
    @{
        Id = "extra_2_covid_personal_growth_summary"
        Type = "Extra - summary extraction"
        Question = "Find an article about recovery or personal growth during the Covid-19 pandemic, and summarise its central argument."
    },
    @{
        Id = "extra_3_author_metadata"
        Type = "Extra - metadata retrieval"
        Question = "Find an article written by Shaunta Grimes about writing or marketing. Return the title and explain briefly why it matches."
    },
    @{
        Id = "extra_4_topic_recommendation"
        Type = "Extra - recommendation"
        Question = "I want an article that gives practical advice for writers who want to grow an audience online. Which article would you recommend, and why?"
    },
    @{
        Id = "extra_5_unknown_fallback"
        Type = "Extra - fallback / insufficient context"
        Question = "According to the dataset, what is the best restaurant in Tokyo for sushi tonight? Answer with the restaurant name only."
    }
)

function Test-PromptSchema {
    param(
        [object]$Result,
        [string]$QuestionId
    )

    $topLevelKeys = @($Result.PSObject.Properties.Name)
    $expectedTopLevel = @("response", "context", "Augmented_prompt")

    foreach ($key in $expectedTopLevel) {
        if ($topLevelKeys -notcontains $key) {
            throw "[$QuestionId] Missing top-level key: $key"
        }
    }

    if ($null -eq $Result.response) {
        throw "[$QuestionId] response is null"
    }

    if ($null -eq $Result.context) {
        throw "[$QuestionId] context is null"
    }

    if ($Result.context.Count -gt 0) {
        $contextKeys = @($Result.context[0].PSObject.Properties.Name)
        $expectedContextKeys = @("article_id", "title", "chunk", "score")

        foreach ($key in $expectedContextKeys) {
            if ($contextKeys -notcontains $key) {
                throw "[$QuestionId] Missing context key: $key"
            }
        }

        if ($contextKeys -contains "authors") {
            throw "[$QuestionId] Public context should not expose authors"
        }

        if ($contextKeys -contains "tags") {
            throw "[$QuestionId] Public context should not expose tags"
        }
    }

    $augmentedKeys = @($Result.Augmented_prompt.PSObject.Properties.Name)
    if ($augmentedKeys -notcontains "System") {
        throw "[$QuestionId] Missing Augmented_prompt.System"
    }

    if ($augmentedKeys -notcontains "User") {
        throw "[$QuestionId] Missing Augmented_prompt.User"
    }

    return $true
}

Write-Host "Testing /api/stats..."
$stats = Invoke-RestMethod -Uri "$BaseUrl/api/stats" -Method Get
$stats | ConvertTo-Json -Depth 10 | Out-File -FilePath "$OutputDir/stats.json" -Encoding UTF8

Write-Host "Stats:"
$stats | ConvertTo-Json -Depth 10
Write-Host ""

foreach ($item in $questions) {
    Write-Host "============================================================"
    Write-Host "Running: $($item.Id)"
    Write-Host "Type: $($item.Type)"
    Write-Host "Question: $($item.Question)"
    Write-Host "============================================================"

    $body = @{
        question = $item.Question
    } | ConvertTo-Json -Depth 10

    try {
        $result = Invoke-RestMethod `
            -Uri "$BaseUrl/api/prompt" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body

        Test-PromptSchema -Result $result -QuestionId $item.Id | Out-Null

        $outputPath = Join-Path $OutputDir "$($item.Id).json"
        $result | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8

        Write-Host "Schema: PASS"
        Write-Host "Response:"
        Write-Host $result.response
        Write-Host ""
        Write-Host "Context titles:"
        foreach ($ctx in $result.context) {
            Write-Host "- [$($ctx.article_id)] $($ctx.title) score=$($ctx.score)"
        }
        Write-Host ""
        Write-Host "Saved full JSON to: $outputPath"
        Write-Host ""
    }
    catch {
        Write-Host "FAILED: $($item.Id)"
        Write-Host $_.Exception.Message
        Write-Host ""
    }
}

Write-Host "Done."
Write-Host "Full JSON outputs saved under: $OutputDir"