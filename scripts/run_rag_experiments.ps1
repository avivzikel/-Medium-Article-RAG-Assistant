param(
    [string]$CsvPath = "data\medium-english-50mb.csv",
    [int]$Limit = 500,
    [int]$BatchSize = 64,
    [switch]$Ingest,
    [string]$OutputCsv = "rag_experiment_results.csv"
)

$ErrorActionPreference = "Stop"

$experiments = @(
    @{
        Name = "exp-384-015-top7"
        ChunkSize = "384"
        OverlapRatio = "0.15"
        TopK = "7"
        Namespace = "exp-384-015"
    },
    @{
        Name = "exp-512-020-top7"
        ChunkSize = "512"
        OverlapRatio = "0.20"
        TopK = "7"
        Namespace = "exp-512-020"
    },
    @{
        Name = "exp-768-020-top7"
        ChunkSize = "768"
        OverlapRatio = "0.20"
        TopK = "7"
        Namespace = "exp-768-020"
    },
    @{
        Name = "exp-512-020-top10"
        ChunkSize = "512"
        OverlapRatio = "0.20"
        TopK = "10"
        Namespace = "exp-512-020-top10"
    }
)

$results = @()

Write-Host "RAG experiment runner"
Write-Host "CSV path: $CsvPath"
Write-Host "Article limit: $Limit"
Write-Host "Batch size: $BatchSize"
Write-Host "Mode: $(if ($Ingest) { 'REAL INGESTION - API COST' } else { 'DRY RUN - NO API COST' })"
Write-Host ""

foreach ($exp in $experiments) {
    Write-Host "========================================"
    Write-Host "Experiment: $($exp.Name)"
    Write-Host "CHUNK_SIZE=$($exp.ChunkSize)"
    Write-Host "OVERLAP_RATIO=$($exp.OverlapRatio)"
    Write-Host "TOP_K=$($exp.TopK)"
    Write-Host "PINECONE_NAMESPACE=$($exp.Namespace)"
    Write-Host "========================================"

    $env:CHUNK_SIZE = $exp.ChunkSize
    $env:OVERLAP_RATIO = $exp.OverlapRatio
    $env:TOP_K = $exp.TopK
    $env:PINECONE_NAMESPACE = $exp.Namespace

    $argsList = @(
        "-m", "scripts.ingest",
        "--csv-path", $CsvPath,
        "--limit", "$Limit",
        "--batch-size", "$BatchSize"
    )

    if (-not $Ingest) {
        $argsList += "--dry-run"
    }

    $output = & python @argsList 2>&1
    $outputText = $output -join "`n"

    Write-Host $outputText
    Write-Host ""

    $loadedArticles = ""
    $createdChunks = ""
    $estimatedBatches = ""

    if ($outputText -match "Loaded\s+(\d+)\s+articles") {
        $loadedArticles = $matches[1]
    }

    if ($outputText -match "Created\s+(\d+)\s+chunks") {
        $createdChunks = $matches[1]
    }

    if ($outputText -match "Estimated batches:\s+(\d+)") {
        $estimatedBatches = $matches[1]
    }

    $results += [PSCustomObject]@{
        experiment = $exp.Name
        namespace = $exp.Namespace
        chunk_size = $exp.ChunkSize
        overlap_ratio = $exp.OverlapRatio
        top_k = $exp.TopK
        article_limit = $Limit
        batch_size = $BatchSize
        mode = $(if ($Ingest) { "ingest" } else { "dry-run" })
        loaded_articles = $loadedArticles
        created_chunks = $createdChunks
        estimated_batches = $estimatedBatches
    }
}

$results | Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8

Write-Host "Saved experiment summary to: $OutputCsv"
Write-Host ""
Write-Host "Important:"
Write-Host "- Dry-run measures chunk counts without embedding cost."
Write-Host "- Real ingestion only happens if you pass -Ingest."
Write-Host "- Chunk size / overlap changes require re-embedding."
Write-Host "- TOP_K changes do not require re-embedding."