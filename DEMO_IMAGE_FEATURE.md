# Demo Image Feature - Hardcoded Results

## Overview
This feature allows you to upload a specific image (Niche Engage ad) and see pre-configured results after a 3-minute loading animation with step-by-step progress.

## Implementation Details

### 1. File Checksum Detection
- **File**: `app/utils/fileChecksum.ts`
- **Purpose**: Calculate SHA-256 checksum of uploaded files to detect the demo image
- **Demo Image Checksum**: `e3c7678e929320af840363de9c204525362a2a35912070fceb18d934aef2bebc`
- **Demo Image Location**: `/Users/sharans/Desktop/projects/AdVisor/i0003.png`

### 2. Loading Modal Component
- **File**: `app/components/AnalysisLoadingModal.tsx`
- **Duration**: 3 minutes (180 seconds total)
- **Steps**:
  1. Uploading creative asset... (20s)
  2. Extracting visual features... (30s)
  3. Analyzing messaging and copy... (25s)
  4. Matching to persona communities... (25s)
  5. Running agent simulations... (40s)
  6. Generating insights... (40s)

### 3. Dashboard Integration
- **File**: `app/dashboard/page.tsx`
- **Changes**:
  - Added checksum calculation on file upload
  - If checksum matches demo image, show loading modal instead of running real analysis
  - After 3 minutes, display hardcoded results

### 4. Hardcoded Results

#### Impact Score
- **Score**: 71 / 100 (Moderately High)

#### Attention Distribution
- **Full**: 46% - Marketing professionals aged 25–40 appreciated the modern, minimalist look
- **Partial**: 39% - Executives (40–55) viewed it as polished but too simple
- **Ignore**: 15% - Younger users (18–25) lost interest due to static layout

#### Key Insights
1. **Visual Design**: The ad performed fairly well with clean, structured design. Dark theme feels professional, but muted colors make key elements blend into the background. Stronger contrast or subtle animation around key metrics could draw focus.

2. **Copy & Messaging**: Clear but slightly formal, lacking emotional pull. Adding short, action-oriented lines beneath each score would make insights feel more personal and motivating.

3. **Demographic Performance**:
   - 46% - Marketing professionals (25–40): Loved modern, minimalist look
   - 24% - Executives (40–55): Polished but too simple, wanted more metrics
   - 15% - Young users (18–25): Lost interest due to static layout
   - 15% - Other demographics: Not relevant or engaging enough

#### Agent Visualization
- **Total Agents**: 932 personas
- **Attention Distribution**:
  - 46% show "full" attention (green nodes)
  - 39% show "neutral" attention (purple nodes)
  - 15% show "ignore" attention (red nodes)

## Usage

### How to Trigger Demo Mode
1. Navigate to the dashboard
2. Click "New Ad Analysis"
3. Upload the image at `/Users/sharans/Desktop/projects/AdVisor/i0003.png`
4. Click "Analyze"
5. Loading modal will appear for 3 minutes
6. After completion, hardcoded results will display

### Backend Configuration
All API endpoints now point to **localhost:8000** instead of EC2:
- `/api/extract` → http://localhost:8000/extract
- `/api/brandmeta` → http://localhost:8000/brandmeta
- `/api/analyze-ad-smart` → http://localhost:8000/api/analyze-ad-smart
- `/api/personas` → http://localhost:8000/api/personas/all

### Environment Variables
Updated `.env`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Files Modified
1. `app/utils/fileChecksum.ts` - New file for SHA-256 checksum calculation
2. `app/components/AnalysisLoadingModal.tsx` - New loading modal component
3. `app/dashboard/page.tsx` - Added checksum detection and hardcoded results
4. `app/api/extract/route.ts` - Changed EC2 URL to localhost
5. `app/api/brandmeta/route.ts` - Changed EC2 URL to localhost
6. `.env` - Changed NEXT_PUBLIC_BACKEND_URL to localhost

## Testing

### Start Backend (if not running)
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend (if not running)
```bash
npm run dev
```

### Verify Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Test Demo Image
1. Open http://localhost:3000/dashboard
2. Upload `i0003.png`
3. Watch 3-minute loading animation
4. Verify hardcoded results appear with Impact Score: 71

## Technical Notes

- **SHA-256 Checksum**: Calculated client-side using Web Crypto API
- **Loading Progress**: Linear progression with step transitions
- **Results Generation**: 932 agents with realistic attention distribution (46/39/15 split)
- **Panel Data**: Includes detailed insights, demographic breakdowns, and specific recommendations
- **No API Calls**: Demo mode bypasses all backend calls during the 3-minute loading period

## Future Enhancements

1. Add more demo images with different checksums
2. Make loading duration configurable
3. Add ability to skip loading animation
4. Create admin panel to configure demo results
5. Support multiple demo scenarios (different industries, ad types)
