-- ============================================================================
-- AdVisor Knowledge Graph Schema
-- ============================================================================
-- This schema defines the core entity and relationship tables for
-- representing personas, communities, interests, and creative preferences.
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE ENTITY TABLES
-- ============================================================================

-- Personas: Audience archetypes derived from community analysis
CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    demographics JSONB, -- age_range, gender, location, income_level, etc.
    psychographics JSONB, -- values, lifestyle, personality_traits, etc.
    pain_points TEXT[], -- array of pain points
    motivations TEXT[], -- array of motivations
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Communities: Subreddits or other online communities
CREATE TABLE IF NOT EXISTS communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL, -- e.g., "r/Fitness"
    platform VARCHAR(100) DEFAULT 'reddit',
    description TEXT,
    member_count INTEGER,
    activity_level VARCHAR(50), -- high, medium, low
    topic_categories TEXT[], -- array of topic tags
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interests: Specific topics, products, or themes
CREATE TABLE IF NOT EXISTS interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    label VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- e.g., "product", "topic", "activity"
    description TEXT,
    keywords TEXT[], -- related search terms
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Creative Preferences: Ad creative attributes that resonate with personas
CREATE TABLE IF NOT EXISTS creative_prefs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    label VARCHAR(255) NOT NULL, -- e.g., "minimalist", "motion_ads", "text_heavy"
    category VARCHAR(100), -- visual_style, format, tone, messaging, etc.
    description TEXT,
    examples JSONB, -- example characteristics or attributes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- RELATIONSHIP TABLES
-- ============================================================================

-- Persona to Community relationships
CREATE TABLE IF NOT EXISTS persona_community (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    relevance_score FLOAT, -- 0.0 to 1.0, how relevant this community is
    context TEXT, -- why this community matters for this persona
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(persona_id, community_id)
);

-- Persona to Interest relationships
CREATE TABLE IF NOT EXISTS persona_interest (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    interest_id UUID NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
    affinity_score FLOAT, -- 0.0 to 1.0, strength of interest
    context TEXT, -- additional context about this interest
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(persona_id, interest_id)
);

-- Persona to Creative Preference relationships
CREATE TABLE IF NOT EXISTS persona_pref (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    pref_id UUID NOT NULL REFERENCES creative_prefs(id) ON DELETE CASCADE,
    importance_score FLOAT, -- 0.0 to 1.0, how important this preference is
    rationale TEXT, -- why this preference matters
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(persona_id, pref_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_personas_name ON personas(name);
CREATE INDEX IF NOT EXISTS idx_communities_name ON communities(name);
CREATE INDEX IF NOT EXISTS idx_interests_label ON interests(label);
CREATE INDEX IF NOT EXISTS idx_creative_prefs_label ON creative_prefs(label);

CREATE INDEX IF NOT EXISTS idx_persona_community_persona ON persona_community(persona_id);
CREATE INDEX IF NOT EXISTS idx_persona_community_community ON persona_community(community_id);
CREATE INDEX IF NOT EXISTS idx_persona_interest_persona ON persona_interest(persona_id);
CREATE INDEX IF NOT EXISTS idx_persona_interest_interest ON persona_interest(interest_id);
CREATE INDEX IF NOT EXISTS idx_persona_pref_persona ON persona_pref(persona_id);
CREATE INDEX IF NOT EXISTS idx_persona_pref_pref ON persona_pref(pref_id);

-- ============================================================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all entity tables
CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interests_updated_at BEFORE UPDATE ON interests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_creative_prefs_updated_at BEFORE UPDATE ON creative_prefs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA
-- ============================================================================

-- Sample Personas
INSERT INTO personas (name, summary, demographics, psychographics, pain_points, motivations)
VALUES
    (
        'Fitness Enthusiasts 18-24',
        'Young adults focused on building muscle and maintaining health on a budget',
        '{"age_range": "18-24", "gender": "mixed", "income_level": "student/entry-level"}'::jsonb,
        '{"values": ["health", "aesthetics", "self-improvement"], "lifestyle": "active", "personality_traits": ["goal-oriented", "community-driven"]}'::jsonb,
        ARRAY['Limited budget', 'Information overload', 'Time constraints'],
        ARRAY['Build muscle', 'Improve appearance', 'Boost confidence']
    ),
    (
        'Busy Professionals 30-45',
        'Career-focused individuals seeking efficient wellness solutions',
        '{"age_range": "30-45", "gender": "mixed", "income_level": "middle-to-upper"}'::jsonb,
        '{"values": ["efficiency", "quality", "work-life-balance"], "lifestyle": "busy", "personality_traits": ["pragmatic", "results-driven"]}'::jsonb,
        ARRAY['Lack of time', 'Stress management', 'Maintaining health while working'],
        ARRAY['Stay healthy', 'Manage stress', 'Maximize limited time']
    ),
    (
        'Gen Z Minimalists',
        'Young consumers who value authenticity and simplicity in design',
        '{"age_range": "18-26", "gender": "mixed", "income_level": "student/entry-level"}'::jsonb,
        '{"values": ["authenticity", "sustainability", "minimalism"], "lifestyle": "digital-native", "personality_traits": ["skeptical of ads", "values-driven"]}'::jsonb,
        ARRAY['Ad fatigue', 'Greenwashing concerns', 'Decision paralysis'],
        ARRAY['Find authentic brands', 'Simplify life', 'Make ethical choices']
    )
ON CONFLICT DO NOTHING;

-- Sample Communities
INSERT INTO communities (name, platform, description, member_count, activity_level, topic_categories)
VALUES
    ('r/Fitness', 'reddit', 'General fitness, workout routines, and nutrition advice', 10000000, 'high', ARRAY['fitness', 'health', 'nutrition']),
    ('r/bodyweightfitness', 'reddit', 'Bodyweight exercises and calisthenics', 2500000, 'high', ARRAY['fitness', 'calisthenics', 'home_workout']),
    ('r/Anxiety', 'reddit', 'Support and discussion for anxiety disorders', 500000, 'high', ARRAY['mental_health', 'support', 'wellness']),
    ('r/minimalism', 'reddit', 'Living with less, intentional living', 1000000, 'medium', ARRAY['lifestyle', 'design', 'philosophy']),
    ('r/motorcycles', 'reddit', 'Motorcycle enthusiasts and riders', 1500000, 'high', ARRAY['vehicles', 'hobby', 'lifestyle'])
ON CONFLICT (name) DO NOTHING;

-- Sample Interests
INSERT INTO interests (label, category, description, keywords)
VALUES
    ('Protein Supplements', 'product', 'Protein powders and supplements for muscle building', ARRAY['whey', 'casein', 'protein powder', 'supplements']),
    ('Budget Gym Memberships', 'service', 'Affordable gym and fitness center options', ARRAY['planet fitness', 'budget gym', 'cheap membership']),
    ('Home Workouts', 'activity', 'Exercise routines that can be done at home', ARRAY['home gym', 'bodyweight', 'no equipment']),
    ('Mental Wellness Apps', 'product', 'Digital tools for meditation and anxiety management', ARRAY['headspace', 'calm', 'meditation', 'therapy']),
    ('Sustainable Fashion', 'product', 'Ethically produced clothing and accessories', ARRAY['sustainable', 'ethical fashion', 'eco-friendly'])
ON CONFLICT DO NOTHING;

-- Sample Creative Preferences
INSERT INTO creative_prefs (label, category, description, examples)
VALUES
    ('Minimalist Design', 'visual_style', 'Clean, simple layouts with lots of white space', '{"colors": ["monochrome", "pastels"], "elements": ["simple typography", "minimal graphics"]}'::jsonb),
    ('Text-Heavy', 'format', 'Ads with substantial copy and detailed explanations', '{"characteristics": ["educational", "informative", "detailed"]}'::jsonb),
    ('Motion Graphics', 'format', 'Animated or video-based advertisements', '{"types": ["short videos", "GIFs", "animated text"]}'::jsonb),
    ('User-Generated Content', 'messaging', 'Content featuring real customers and testimonials', '{"elements": ["reviews", "before-after", "testimonials"]}'::jsonb),
    ('Bold & Colorful', 'visual_style', 'Vibrant colors and eye-catching visuals', '{"colors": ["bright", "contrasting"], "elements": ["bold typography", "graphics"]}'::jsonb)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- LINK PERSONAS TO ENTITIES (Sample Relationships)
-- ============================================================================

-- Fitness Enthusiasts 18-24 relationships
INSERT INTO persona_community (persona_id, community_id, relevance_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Fitness Enthusiasts 18-24'),
    c.id,
    CASE c.name
        WHEN 'r/Fitness' THEN 0.95
        WHEN 'r/bodyweightfitness' THEN 0.85
        ELSE 0.5
    END,
    'Primary community for fitness content'
FROM communities c
WHERE c.name IN ('r/Fitness', 'r/bodyweightfitness')
ON CONFLICT DO NOTHING;

INSERT INTO persona_interest (persona_id, interest_id, affinity_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Fitness Enthusiasts 18-24'),
    i.id,
    0.9,
    'High interest due to budget constraints and muscle-building goals'
FROM interests i
WHERE i.label IN ('Protein Supplements', 'Budget Gym Memberships', 'Home Workouts')
ON CONFLICT DO NOTHING;

INSERT INTO persona_pref (persona_id, pref_id, importance_score, rationale)
SELECT
    (SELECT id FROM personas WHERE name = 'Fitness Enthusiasts 18-24'),
    cp.id,
    CASE cp.label
        WHEN 'User-Generated Content' THEN 0.9
        WHEN 'Bold & Colorful' THEN 0.75
        ELSE 0.6
    END,
    'Resonates with peer influence and energetic visual style'
FROM creative_prefs cp
WHERE cp.label IN ('User-Generated Content', 'Bold & Colorful')
ON CONFLICT DO NOTHING;

-- Gen Z Minimalists relationships
INSERT INTO persona_community (persona_id, community_id, relevance_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Gen Z Minimalists'),
    c.id,
    0.9,
    'Core community for minimalist lifestyle'
FROM communities c
WHERE c.name = 'r/minimalism'
ON CONFLICT DO NOTHING;

INSERT INTO persona_interest (persona_id, interest_id, affinity_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Gen Z Minimalists'),
    i.id,
    0.85,
    'Aligns with minimalist and sustainable values'
FROM interests i
WHERE i.label = 'Sustainable Fashion'
ON CONFLICT DO NOTHING;

INSERT INTO persona_pref (persona_id, pref_id, importance_score, rationale)
SELECT
    (SELECT id FROM personas WHERE name = 'Gen Z Minimalists'),
    cp.id,
    0.95,
    'Strong preference for clean, simple design aesthetic'
FROM creative_prefs cp
WHERE cp.label = 'Minimalist Design'
ON CONFLICT DO NOTHING;

-- Busy Professionals relationships
INSERT INTO persona_community (persona_id, community_id, relevance_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Busy Professionals 30-45'),
    c.id,
    0.8,
    'Relevant for stress and wellness management'
FROM communities c
WHERE c.name IN ('r/Anxiety', 'r/Fitness')
ON CONFLICT DO NOTHING;

INSERT INTO persona_interest (persona_id, interest_id, affinity_score, context)
SELECT
    (SELECT id FROM personas WHERE name = 'Busy Professionals 30-45'),
    i.id,
    0.85,
    'Solutions for time-constrained wellness'
FROM interests i
WHERE i.label IN ('Mental Wellness Apps', 'Home Workouts')
ON CONFLICT DO NOTHING;

INSERT INTO persona_pref (persona_id, pref_id, importance_score, rationale)
SELECT
    (SELECT id FROM personas WHERE name = 'Busy Professionals 30-45'),
    cp.id,
    0.8,
    'Prefers clear, informative content over flashy designs'
FROM creative_prefs cp
WHERE cp.label IN ('Text-Heavy', 'Minimalist Design')
ON CONFLICT DO NOTHING;
