# Community Mapping Implementation

## Overview
Implemented community display name mapping for the AgentGraph visualization, allowing users to see friendly community names (e.g., "Fitness Enthusiasts") instead of generic labels (e.g., "Community 01").

## Changes Made

### 1. Backend API Update ([backend/api/routes/personas.py](backend/api/routes/personas.py))

**Added:**
- `COMMUNITY_DISPLAY_NAMES` dictionary mapping subreddit names to display names:
  - `r/Fitness` → `Fitness Enthusiasts`
  - `r/Anxiety` → `Mental Health Advocates`
  - `r/minimalism` → `College Students on a Budget`
  - `r/motorcycles` → `Automotive Hobbyists`
  - `r/pokemon` → `Avid Gamers`
  - And 20 more mappings...

**Updated `/api/personas/all` endpoint:**
- Now joins `personas` with `persona_community` and `communities` tables
- Returns `community_name` (original subreddit) and `community_display_name` for each persona
- Returns `communities` array with list of unique display names

**Response format:**
```json
{
  "personas": [
    {
      "id": "...",
      "name": "...",
      "community_name": "r/Fitness",
      "community_display_name": "Fitness Enthusiasts",
      ...
    }
  ],
  "total": 932,
  "communities": [
    "Avid Gamers",
    "Automotive Hobbyists",
    "College Students on a Budget",
    ...
  ]
}
```

### 2. Frontend AgentGraph Component ([app/components/AgentGraph.tsx](app/components/AgentGraph.tsx))

**Added state:**
- `communityNames: string[]` - List of unique community display names from API
- `communityIndexMap: Map<string, number>` - Maps display name to numeric index for graph coloring

**Updated AgentNode type:**
- Added `community_name?: string` (e.g., "r/Fitness")
- Added `community_display_name?: string` (e.g., "Fitness Enthusiasts")

**Updated persona fetch logic:**
- Extracts `communities` array from API response
- Creates index mapping (display name → 0-19 index)
- Logs loaded communities for debugging

**Updated nodes generation:**
- Assigns `community` index based on `community_display_name` using `communityIndexMap`
- Stores both `community_name` and `community_display_name` on each node

**Updated UI labels:**
- Legend chips now show community display names (e.g., "Fitness Enthusiasts") instead of "Community 01"
- Hover tooltip shows community display name
- Click card shows community display name
- Falls back to "Community XX" if display name not available

## Community Mapping Table

| Subreddit | Display Name |
|-----------|-------------|
| r/Fitness | Fitness Enthusiasts |
| r/bodyweightfitness | Fitness Enthusiasts |
| r/Anxiety | Mental Health Advocates |
| r/minimalism | College Students on a Budget |
| r/motorcycles | Automotive Hobbyists |
| r/ProRevenge | Movie Buffs |
| r/tifu | Movie Buffs |
| r/relationship_advice | Mental Health Advocates |
| r/MaliciousCompliance | Movie Buffs |
| r/BestofRedditorUpdates | Movie Buffs |
| r/pokemon | Avid Gamers |
| r/CuratedTumblr | Fashion Enthusiasts |
| r/YouShouldKnow | Personal Finance Planners |
| r/science | Science & Tech Explorers |
| r/AmItheAsshole | Mental Health Advocates |
| r/LifeProTips | Personal Finance Planners |
| r/todayilearned | Science & Tech Explorers |
| r/Showerthoughts | Science & Tech Explorers |
| r/politics | Science & Tech Explorers |
| r/mildlyinfuriating | Movie Buffs |
| r/pics | Photography Creators |
| r/cats | Pet Parents |
| r/nosleep | Movie Buffs |
| r/onebag | Outdoor Adventurers |
| r/funny | Movie Buffs |

## How It Works

1. **Backend**: When fetching personas, the API joins with `persona_community` and `communities` tables to get the subreddit name for each persona
2. **Mapping**: The subreddit name is mapped to a friendly display name using `COMMUNITY_DISPLAY_NAMES`
3. **Frontend**: The display names are used to create a community index mapping (0-19)
4. **Visualization**: Each persona is assigned to a community index based on its display name
5. **Filtering**: When a user clicks a community chip, all personas in that community are highlighted

## Testing

To verify the implementation:

1. Start the backend: `cd backend && python3 -m uvicorn main:app --reload`
2. Check API response: `curl http://localhost:8000/api/personas/all`
3. Open frontend dashboard and verify:
   - Legend shows community display names
   - Clicking a community filters personas
   - Hovering shows correct community name
   - All personas with same community display name are grouped together

## Next Steps

- Ensure Supabase RLS policies allow service role to insert/update (see [SUPABASE_RLS_FIX.md](SUPABASE_RLS_FIX.md))
- Test community filtering with actual ad analysis
- Verify all 932 personas are correctly mapped to their communities
