# Findaway Chapter Workflow Implementation

## Overview

This document describes the comprehensive chapter workflow system implemented for Findaway-compliant audiobook generation. The system allows users to review, reorder, and approve chapters before audio generation, with strict segment ordering for Findaway distribution.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER UPLOADS MANUSCRIPT                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CHAPTER PARSING (chapter_parser.py)                 │
│  - Detect chapter headings (CHAPTER 1, Chapter One, Part I, etc.)       │
│  - Classify segment types (front_matter, body_chapter, back_matter)     │
│  - Calculate segment_order (0, 1-9, 10-79, 80-89, 98, 99)              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  JOB STATUS: chapters_pending                           │
│                  USER REVIEWS CHAPTERS (ChapterReview.tsx)              │
│  - Drag-and-drop reordering                                             │
│  - Include/exclude chapters                                             │
│  - Change segment types                                                 │
│  - View word counts and duration estimates                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  JOB STATUS: chapters_approved                          │
│                  TTS GENERATION (per chapter)                           │
│  - Generate audio for each approved chapter                             │
│  - Create tracks with Findaway-style filenames                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  JOB STATUS: completed                                  │
│                  DOWNLOADS (TracksView.tsx)                             │
│  - Per-track download                                                   │
│  - Download All (ZIP)                                                   │
│  - Findaway-ready filenames                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Findaway Segment Ordering

The system uses strict segment ordering for Findaway distribution compatibility:

| Segment Type      | segment_order | Max Count | Example Filename         |
|-------------------|---------------|-----------|--------------------------|
| Opening Credits   | 0             | 1         | `00_opening_credits.mp3` |
| Front Matter      | 1-9           | 9         | `01_front_matter_01.mp3` |
| Body Chapters     | 10-79         | 70        | `10_chapter_01.mp3`      |
| Back Matter       | 80-89         | 10        | `80_back_matter_01.mp3`  |
| Closing Credits   | 98            | 1         | `98_closing_credits.mp3` |
| Retail Sample     | 99            | 1         | `99_retail_sample.mp3`   |

## Database Schema

### chapters Table

```sql
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Ordering
    chapter_index INTEGER NOT NULL,      -- Final playback order (reorderable)
    source_order INTEGER NOT NULL,       -- Original manuscript order (immutable)
    segment_order INTEGER,               -- Findaway order (0, 1-9, 10-79, 80-89, 98, 99)

    -- Content
    title TEXT NOT NULL DEFAULT 'Untitled',
    display_title TEXT,                  -- Clean title for UI
    text_content TEXT,                   -- Full chapter text

    -- Classification
    segment_type TEXT NOT NULL DEFAULT 'body_chapter'
        CHECK (segment_type IN (
            'opening_credits', 'front_matter', 'body_chapter',
            'back_matter', 'closing_credits', 'retail_sample'
        )),

    -- Status
    status TEXT NOT NULL DEFAULT 'pending_review'
        CHECK (status IN (
            'pending_review', 'approved', 'excluded',
            'processing', 'completed', 'failed'
        )),

    -- Statistics
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER DEFAULT 0,

    -- Audio output
    audio_path TEXT,
    audio_duration_seconds INTEGER,
    audio_file_size_bytes BIGINT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Unique constraint: no duplicate segment_orders per job
CREATE UNIQUE INDEX idx_chapters_job_segment_order ON chapters(job_id, segment_order);
```

### tracks Table

```sql
CREATE TABLE tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,

    track_index INTEGER NOT NULL,
    segment_order INTEGER,
    title TEXT NOT NULL,
    segment_type TEXT NOT NULL DEFAULT 'body_chapter',
    export_filename TEXT,                -- e.g., "10_chapter_01.mp3"

    audio_path TEXT,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,

    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### retail_samples Table

```sql
CREATE TABLE retail_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    source_chapter_id UUID REFERENCES chapters(id),

    sample_text TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER DEFAULT 0,

    -- AI scoring (from Gemini analysis)
    engagement_score NUMERIC(3,2),           -- 0.00 to 1.00
    emotional_intensity_score NUMERIC(3,2),
    spoiler_risk_score NUMERIC(3,2),
    overall_score NUMERIC(3,2),

    -- Selection status
    is_auto_suggested BOOLEAN DEFAULT TRUE,
    is_user_confirmed BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,
    user_edited_text TEXT,
    candidate_rank INTEGER DEFAULT 1,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ
);
```

## Backend Implementation

### Chapter Parser (apps/engine/core/chapter_parser.py)

The chapter parser detects and classifies chapters from manuscript text:

```python
def split_into_chapters(text: str, mode: str = "auto") -> List[Dict]:
    """
    Split manuscript text into chapters with segment classification.

    Returns list of dicts with:
    - title: Chapter title
    - text: Chapter content
    - segment_type: front_matter, body_chapter, or back_matter
    - source_order: Original position in manuscript
    """
    # Detect chapter headings using multiple patterns:
    # - "CHAPTER 1", "Chapter 1", "CHAPTER ONE"
    # - "Part I", "PART ONE"
    # - "Prologue", "Epilogue", "Afterword", etc.

    chapters = []
    # ... parsing logic ...

    # Classify each chapter
    for chapter in chapters:
        chapter["segment_type"] = classify_segment_type(chapter["title"])

    return chapters


def classify_segment_type(title: str) -> str:
    """
    Classify a chapter title into Findaway segment types.

    Front matter: Dedication, Foreword, Preface, Introduction, Prologue
    Back matter: Epilogue, Afterword, Appendix, Acknowledgments, About the Author
    Body chapter: Everything else (Chapter 1, Part I, etc.)
    """
    title_lower = title.lower().strip()

    front_matter_keywords = [
        "dedication", "foreword", "preface", "introduction",
        "prologue", "author's note", "note from the author"
    ]

    back_matter_keywords = [
        "epilogue", "afterword", "appendix", "acknowledgment",
        "about the author", "biography", "glossary", "index",
        "notes", "bibliography", "resources"
    ]

    for keyword in front_matter_keywords:
        if keyword in title_lower:
            return "front_matter"

    for keyword in back_matter_keywords:
        if keyword in title_lower:
            return "back_matter"

    return "body_chapter"


def calculate_segment_order(segment_type: str, index_within_type: int) -> int:
    """
    Calculate the Findaway segment_order for a chapter.

    Segment order ranges:
    - 0: Opening credits
    - 1-9: Front matter (up to 9 items)
    - 10-79: Body chapters (up to 70 chapters)
    - 80-89: Back matter (up to 10 items)
    - 98: Closing credits
    - 99: Retail sample
    """
    if segment_type == "opening_credits":
        return 0
    elif segment_type == "front_matter":
        return min(1 + index_within_type, 9)
    elif segment_type == "body_chapter":
        return min(10 + index_within_type, 79)
    elif segment_type == "back_matter":
        return min(80 + index_within_type, 89)
    elif segment_type == "closing_credits":
        return 98
    elif segment_type == "retail_sample":
        return 99
    else:
        return min(10 + index_within_type, 79)


def generate_findaway_filename(
    segment_type: str,
    index_within_type: int,
    title: str,
    extension: str = "mp3"
) -> str:
    """
    Generate Findaway-compliant filename.

    Examples:
    - generate_findaway_filename("opening_credits", 0, "Opening")
      → "00_opening_credits.mp3"
    - generate_findaway_filename("body_chapter", 0, "Chapter 1")
      → "10_chapter_01.mp3"
    - generate_findaway_filename("back_matter", 1, "Afterword")
      → "81_back_matter_02.mp3"
    """
    segment_order = calculate_segment_order(segment_type, index_within_type)

    if segment_type == "opening_credits":
        return f"00_opening_credits.{extension}"
    elif segment_type == "front_matter":
        return f"{segment_order:02d}_front_matter_{index_within_type + 1:02d}.{extension}"
    elif segment_type == "body_chapter":
        return f"{segment_order:02d}_chapter_{index_within_type + 1:02d}.{extension}"
    elif segment_type == "back_matter":
        return f"{segment_order:02d}_back_matter_{index_within_type - 79:02d}.{extension}"
    elif segment_type == "closing_credits":
        return f"98_closing_credits.{extension}"
    elif segment_type == "retail_sample":
        return f"99_retail_sample.{extension}"
    else:
        return f"{segment_order:02d}_unknown.{extension}"
```

### Retail Sample Selector (apps/engine/core/retail_sample_selector.py)

AI-powered retail sample selection using Gemini:

```python
def select_retail_sample(
    chapters: List[Dict],
    max_chapters_to_analyze: int = 3,
    use_ai: bool = True
) -> Dict:
    """
    Select the best excerpt for a retail sample.

    Criteria for "spicy" romance samples:
    - 400-900 words (3-5 minutes of audio)
    - High engagement/emotional intensity
    - Low spoiler risk
    - Strong hook that makes listeners want more

    Returns:
        {
            "excerpt_text": str,
            "source_chapter_index": int,
            "source_chapter_title": str,
            "word_count": int,
            "scores": {
                "engagement": 0.0-1.0,
                "emotional_intensity": 0.0-1.0,
                "spoiler_risk": 0.0-1.0,
                "overall": 0.0-1.0
            },
            "candidates": [...]  # Alternative excerpts
        }
    """
    if use_ai:
        return _select_with_ai(chapters, max_chapters_to_analyze)
    else:
        return _select_heuristic(chapters)


def _select_with_ai(chapters: List[Dict], max_chapters: int) -> Dict:
    """Use Gemini to analyze and score potential excerpts."""
    import google.generativeai as genai

    # Only analyze first N chapters (avoid spoilers)
    chapters_to_analyze = chapters[:max_chapters]

    prompt = """
    Analyze this chapter excerpt for use as an audiobook retail sample.

    Score each of these criteria from 0.0 to 1.0:
    1. ENGAGEMENT: How compelling/interesting is this passage?
    2. EMOTIONAL_INTENSITY: How emotionally charged is the content?
    3. SPOILER_RISK: How much plot does this reveal? (0=safe, 1=major spoilers)

    Also identify the best 400-900 word excerpt within this text.

    Chapter text:
    {chapter_text}

    Respond in JSON format:
    {
        "engagement": 0.85,
        "emotional_intensity": 0.72,
        "spoiler_risk": 0.15,
        "best_excerpt_start": 0,
        "best_excerpt_end": 500,
        "reasoning": "..."
    }
    """

    # Analyze each chapter and pick the best excerpt
    # ...
```

### API Endpoints (apps/engine/api/main.py)

#### Chapter Management

```python
@app.get("/jobs/{job_id}/chapters")
async def get_job_chapters(job_id: str, user_id: str = Depends(get_current_user)):
    """Get all chapters for a job."""
    # Returns chapters sorted by chapter_index

@app.patch("/jobs/{job_id}/chapters/{chapter_id}")
async def update_chapter(
    job_id: str,
    chapter_id: str,
    request: ChapterUpdateRequest,
    user_id: str = Depends(get_current_user)
):
    """Update chapter title, segment_type, or status."""

@app.post("/jobs/{job_id}/chapters/reorder")
async def reorder_chapters(
    job_id: str,
    request: ReorderChaptersRequest,  # {"new_order": ["id1", "id2", ...]}
    user_id: str = Depends(get_current_user)
):
    """Reorder chapters by providing new order of IDs."""

@app.post("/jobs/{job_id}/chapters/approve")
async def approve_chapters(
    job_id: str,
    request: ApproveChaptersRequest = None,  # Optional: specific chapter IDs
    user_id: str = Depends(get_current_user)
):
    """Approve chapters and start TTS generation."""
    # 1. Update job status to 'chapters_approved'
    # 2. Mark chapters as 'approved'
    # 3. Enqueue job for TTS processing
```

#### Retail Sample Management

```python
@app.get("/jobs/{job_id}/retail-samples")
async def get_retail_samples(job_id: str, user_id: str = Depends(get_current_user)):
    """Get retail sample candidates for a job."""

@app.post("/jobs/{job_id}/retail-samples/confirm")
async def confirm_retail_sample(
    job_id: str,
    request: ConfirmRetailSampleRequest,
    user_id: str = Depends(get_current_user)
):
    """Confirm a retail sample selection."""
```

#### Track Downloads

```python
@app.get("/jobs/{job_id}/tracks")
async def get_job_tracks(job_id: str, user_id: str = Depends(get_current_user)):
    """Get all tracks for a completed job."""

@app.get("/jobs/{job_id}/tracks/{track_id}/download")
async def download_track(
    job_id: str,
    track_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get presigned download URL for a track."""
```

## Frontend Implementation

### ChapterReview Component (apps/web/components/chapters/ChapterReview.tsx)

```tsx
interface ChapterReviewProps {
  job: Job
  onApproved: (updatedJob: Job) => void
}

export function ChapterReview({ job, onApproved }: ChapterReviewProps) {
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch chapters on mount
  useEffect(() => {
    const fetchChapters = async () => {
      const data = await getJobChapters(job.id)
      setChapters(data)
      setLoading(false)
    }
    fetchChapters()
  }, [job.id])

  // Handle drag-and-drop reordering
  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return

    const reordered = Array.from(chapters)
    const [moved] = reordered.splice(result.source.index, 1)
    reordered.splice(result.destination.index, 0, moved)

    setChapters(reordered)

    // Persist to backend
    await reorderChapters(job.id, reordered.map(c => c.id))
  }

  // Handle segment type change
  const handleSegmentTypeChange = async (chapterId: string, newType: string) => {
    await updateChapter(job.id, chapterId, { segment_type: newType })
    // Refresh chapters
  }

  // Handle include/exclude toggle
  const handleExcludeToggle = async (chapterId: string, exclude: boolean) => {
    await updateChapter(job.id, chapterId, {
      status: exclude ? 'excluded' : 'pending_review'
    })
  }

  // Handle approval
  const handleApprove = async () => {
    const approvedChapterIds = chapters
      .filter(c => c.status !== 'excluded')
      .map(c => c.id)

    const updatedJob = await approveChapters(job.id, approvedChapterIds)
    onApproved(updatedJob)
  }

  return (
    <div>
      <h2>Review Chapters</h2>

      {/* Chapter list with drag-and-drop */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="chapters">
          {(provided) => (
            <div {...provided.droppableProps} ref={provided.innerRef}>
              {chapters.map((chapter, index) => (
                <Draggable key={chapter.id} draggableId={chapter.id} index={index}>
                  {(provided) => (
                    <div ref={provided.innerRef} {...provided.draggableProps}>
                      <span {...provided.dragHandleProps}>⋮⋮</span>
                      <span>{chapter.title}</span>
                      <span>{chapter.word_count} words</span>
                      <select
                        value={chapter.segment_type}
                        onChange={(e) => handleSegmentTypeChange(chapter.id, e.target.value)}
                      >
                        <option value="front_matter">Front Matter</option>
                        <option value="body_chapter">Body Chapter</option>
                        <option value="back_matter">Back Matter</option>
                      </select>
                      <button onClick={() => handleExcludeToggle(chapter.id, true)}>
                        Exclude
                      </button>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>

      {/* Summary */}
      <div>
        <p>Total chapters: {chapters.filter(c => c.status !== 'excluded').length}</p>
        <p>Estimated duration: {formatDuration(totalDuration)}</p>
      </div>

      {/* Approve button */}
      <button onClick={handleApprove}>
        Generate Audio
      </button>
    </div>
  )
}
```

### TracksView Component (apps/web/components/tracks/TracksView.tsx)

```tsx
interface TracksViewProps {
  job: Job
}

export function TracksView({ job }: TracksViewProps) {
  const [tracks, setTracks] = useState<Track[]>([])

  useEffect(() => {
    const fetchTracks = async () => {
      const data = await getJobTracks(job.id)
      setTracks(data)
    }
    fetchTracks()
  }, [job.id])

  const handleDownloadTrack = async (trackId: string) => {
    const { url } = await getTrackDownloadUrl(job.id, trackId)
    window.open(url, '_blank')
  }

  const handleDownloadAll = async () => {
    const { url } = await getJobDownloadUrl(job.id)
    window.open(url, '_blank')
  }

  return (
    <div>
      <h2>Audio Tracks</h2>

      {/* Findaway-ready banner */}
      <div className="info-banner">
        These files are named for Findaway distribution.
        Upload them directly to your Findaway account.
      </div>

      {/* Track list */}
      <div>
        {tracks.map((track) => (
          <div key={track.id}>
            <span>{track.export_filename}</span>
            <span>{track.title}</span>
            <span>{formatDuration(track.duration_seconds)}</span>
            <button onClick={() => handleDownloadTrack(track.id)}>
              Download
            </button>
          </div>
        ))}
      </div>

      {/* Download All button */}
      <button onClick={handleDownloadAll}>
        Download All (ZIP)
      </button>
    </div>
  )
}
```

## API Client (apps/web/lib/apiClient.ts)

```typescript
// Chapter types
export interface Chapter {
  id: string
  job_id: string
  chapter_index: number
  source_order: number
  segment_order?: number
  title: string
  display_title?: string
  text_content?: string
  segment_type: 'opening_credits' | 'front_matter' | 'body_chapter' |
                'back_matter' | 'closing_credits' | 'retail_sample'
  status: 'pending_review' | 'approved' | 'excluded' |
          'processing' | 'completed' | 'failed'
  word_count: number
  character_count: number
  estimated_duration_seconds: number
  audio_path?: string
  audio_duration_seconds?: number
  created_at: string
  updated_at: string
}

// Track types
export interface Track {
  id: string
  job_id: string
  chapter_id?: string
  track_index: number
  segment_order?: number
  title: string
  segment_type: string
  export_filename?: string
  audio_path?: string
  duration_seconds?: number
  file_size_bytes?: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

// API functions
export async function getJobChapters(jobId: string): Promise<Chapter[]> {
  return fetchApi<Chapter[]>(`/jobs/${jobId}/chapters`)
}

export async function updateChapter(
  jobId: string,
  chapterId: string,
  data: Partial<Chapter>
): Promise<Chapter> {
  return fetchApi<Chapter>(`/jobs/${jobId}/chapters/${chapterId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function reorderChapters(
  jobId: string,
  newOrder: string[]
): Promise<Chapter[]> {
  return fetchApi<Chapter[]>(`/jobs/${jobId}/chapters/reorder`, {
    method: 'POST',
    body: JSON.stringify({ new_order: newOrder }),
  })
}

export async function approveChapters(
  jobId: string,
  chapterIds?: string[]
): Promise<Job> {
  return fetchApi<Job>(`/jobs/${jobId}/chapters/approve`, {
    method: 'POST',
    body: JSON.stringify({ chapter_ids: chapterIds }),
  })
}

export async function getJobTracks(jobId: string): Promise<Track[]> {
  return fetchApi<Track[]>(`/jobs/${jobId}/tracks`)
}

export async function getTrackDownloadUrl(
  jobId: string,
  trackId: string
): Promise<{ url: string }> {
  return fetchApi<{ url: string }>(`/jobs/${jobId}/tracks/${trackId}/download`)
}
```

## Job Status Flow

```
pending
    │
    ▼
parsing ─────────────────► failed
    │
    ▼
chapters_pending ─────────► cancelled
    │
    │ (user approves)
    ▼
chapters_approved ────────► failed
    │
    │ (TTS processing)
    ▼
processing ───────────────► failed
    │
    ▼
completed
```

## What Was Removed

### Cover Art Generation (Phase 5)

The following cover art functionality was removed as it should be handled by a dedicated service:

- **Deleted**: `apps/engine/core/cover_generator.py`
  - OpenAI DALL-E integration
  - Banana.dev SDXL/Flux integration
  - Cover prompt generation

- **Removed from API**:
  - `GET /jobs/{job_id}/cover` endpoint
  - Cover art fields from `JobCreateRequest`
  - Cover art fields from `JobResponse`
  - `banana_cover_enabled` from system status

- **Removed from Frontend**:
  - Cover art options in dashboard
  - Cover vibe selection
  - Custom cover description field

## Files Changed

### New Files Created
- `supabase/migrations/0007_chapters_table.sql`
- `supabase/migrations/0008_findaway_segment_order.sql`
- `apps/engine/core/retail_sample_selector.py`
- `apps/web/components/chapters/ChapterReview.tsx`
- `apps/web/components/chapters/index.ts`
- `apps/web/components/tracks/TracksView.tsx`
- `apps/web/components/tracks/index.ts`

### Modified Files
- `apps/engine/core/chapter_parser.py` - Added segment ordering functions
- `apps/engine/core/__init__.py` - Export new functions
- `apps/engine/api/main.py` - Added chapter/track/retail sample endpoints
- `apps/engine/pipelines/findaway_pipeline.py` - Removed cover generation
- `apps/web/lib/apiClient.ts` - Added chapter/track types and functions
- `apps/web/app/job/[id]/page.tsx` - Added ChapterReview and TracksView
- `apps/web/app/library/page.tsx` - Updated status displays
- `apps/web/app/dashboard/page.tsx` - Removed cover art UI

### Deleted Files
- `apps/engine/core/cover_generator.py`

---

## Latest Updates (November 2025)

### Job Detail Page - Multi-Step Flow Indicator

The job detail page now includes a visual step indicator showing the audiobook generation workflow:

```
📄 Upload & Parse → 📋 Review Chapters → 🎙️ Generate Audio → 📦 Export & Download
```

Each step is highlighted based on the job status with:
- ✅ Green checkmark for completed steps
- 🔵 Purple pulse animation for current step
- ⬜ Gray for pending steps
- 🔴 Red for error states (failed/cancelled)

**Location**: `apps/web/app/job/[id]/page.tsx`

### Enhanced ChapterReview Component

The chapter review UI has been polished with:

```tsx
// Key features:
- Summary stats header (chapters count, word count, estimated duration)
- Drag-and-drop reordering with visual feedback (ring + glow effect)
- Order number display in rounded badge
- Segment type dropdown (Front Matter / Chapter / Back Matter)
- Chapter text preview expansion
- Include/Exclude toggle with color-coded icons
- Validation: requires at least one body chapter
- Save indicator showing when changes are being persisted
```

**Visual design**:
- Uses `GlassCard` with `glow` prop for header
- Segment type badges with color coding:
  - Blue: Front Matter
  - Purple: Chapter
  - Amber: Back Matter
- Status badges for excluded chapters

### RetailSampleReview Component

New component for reviewing AI-selected retail samples:

```tsx
interface RetailSampleReviewProps {
  job: Job
  onConfirmed?: (sample: RetailSample) => void
  onSkip?: () => void
}

// Features:
- Display multiple sample candidates from AI
- AI scoring display (engagement, emotion, spoiler risk)
- Text preview with editing capability
- Regenerate samples with different styles
- Confirm sample selection
```

**API Endpoints Added**:
```python
# PATCH /jobs/{job_id}/retail-samples/{sample_id}
# Updates user_edited_text field
class RetailSampleUpdateRequest(BaseModel):
    user_edited_text: Optional[str] = None

# POST /jobs/{job_id}/retail-samples/regenerate
# Generates new AI sample candidates
```

**Location**: `apps/web/components/chapters/RetailSampleReview.tsx`

### Enhanced TracksView Component

The tracks view now includes:

```tsx
// Key features:
- Summary stats (tracks ready, total duration, total size)
- Processing indicator for tracks still generating
- Audio preview player with play/pause
- Individual track download buttons
- Download All (ZIP) primary action
- Findaway-ready banner when complete
- Status badges per track (Ready, Generating, Queued, Failed)
```

**Visual design**:
- Track number in rounded badge
- Play button with hover states
- Segment type color coding consistent with chapters
- Glow effect on header when all tracks complete

### Updated Type Definitions

```typescript
// apps/web/lib/apiClient.ts

export interface Chapter {
  id: string
  job_id: string
  chapter_index: number
  source_order: number
  segment_order?: number      // NEW: Findaway order
  title: string
  display_title?: string      // NEW: Clean display title
  text_content?: string
  // ... status, segment_type, etc.
  audio_file_size_bytes?: number  // NEW
  approved_at?: string        // NEW
  completed_at?: string       // NEW
}

export interface RetailSample {
  // ... existing fields ...
  user_edited_text?: string   // NEW: Edited text
  candidate_rank?: number     // NEW: Ranking among candidates
}
```

### Polling & Status Updates

The job detail page now polls for updates when:
- Status is `parsing`, `pending`, `chapters_approved`, or `processing`
- Shows "Updating..." indicator with pulsing dot
- Auto-refreshes every 5 seconds
- Stops polling when job completes or fails

---

## Testing the Full Workflow

1. **Upload a manuscript** with chapters (TXT, DOCX, or Google Doc)

2. **Wait for parsing** - Job enters `parsing` status
   - Watch the step indicator show "Upload & Parse" as current
   - Progress bar shows parsing progress

3. **Review chapters** (Job enters `chapters_pending`)
   - Drag to reorder chapters
   - Change segment types (Front Matter, Chapter, Back Matter)
   - Exclude chapters you don't want
   - Preview chapter text with eye icon
   - Check summary stats (words, duration)

4. **Approve chapters** - Click "Approve & Generate Audio"
   - Button shows loading state
   - Job enters `chapters_approved` then `processing`

5. **Monitor generation** - Watch progress bar
   - Step indicator shows "Generate Audio" as current
   - Auto-refresh shows real-time progress

6. **Review retail sample** (when complete)
   - See AI-suggested excerpts with scores
   - Edit text if needed
   - Approve your preferred sample

7. **Download tracks**
   - Preview individual tracks with audio player
   - Download single tracks or full ZIP
   - Tracks use Findaway-compatible filenames

---

## User Tasks to Complete

To fully enable this workflow, ensure the following are configured:

### 1. Database Migrations
You mentioned SQL is already applied to Supabase. If you need to verify, check that these tables exist:
- `chapters` - with `segment_order`, `display_title` columns
- `tracks` - with `export_filename` column
- `retail_samples` - with `user_edited_text`, `candidate_rank` columns

### 2. Environment Variables
Your existing environment variables should already be configured:
- `OPENAI_API_KEY` - Already set (used for TTS)
- `SUPABASE_URL` - Already set
- `SUPABASE_SERVICE_ROLE_KEY` - Already set

### 3. Verify Backend Endpoints
The following new endpoints should be available:
```
GET  /jobs/{job_id}/chapters
PATCH /jobs/{job_id}/chapters/{chapter_id}
POST /jobs/{job_id}/chapters/reorder
POST /jobs/{job_id}/chapters/approve
GET  /jobs/{job_id}/retail-samples
PATCH /jobs/{job_id}/retail-samples/{sample_id}
POST /jobs/{job_id}/retail-samples/regenerate
POST /jobs/{job_id}/retail-samples/confirm
GET  /jobs/{job_id}/tracks
GET  /jobs/{job_id}/tracks/{track_id}/download
GET  /jobs/{job_id}/download
```

---

## Files Modified in This Update

### Frontend (apps/web)
- `app/job/[id]/page.tsx` - Multi-step flow, polling, retail sample integration
- `components/chapters/ChapterReview.tsx` - Enhanced UX, summary stats, save indicator
- `components/chapters/RetailSampleReview.tsx` - New component for retail samples
- `components/chapters/index.ts` - Export RetailSampleReview
- `components/tracks/TracksView.tsx` - Enhanced with status, preview, stats
- `lib/apiClient.ts` - Updated types, new API functions

### Backend (apps/engine)
- `api/main.py` - Added PATCH and regenerate retail sample endpoints
- `api/main.py` - Added user_edited_text, candidate_rank to RetailSampleResponse

---

**Last Updated:** 2025-11-29
**Migration Version:** 0008
**Frontend Version:** Enhanced chapter workflow UI
