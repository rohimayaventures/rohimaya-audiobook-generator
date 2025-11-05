# �� Integration Guide - Rohimaya Platform

## Overview

This guide explains how to integrate the Audiobook Generator into the main Rohimaya Publishing platform.

---

## 🎯 Integration Scenarios

### Scenario 1: Standalone App (Current)
**Status:** ✅ Complete  
**Use Case:** Beta testing, demos  
**URL:** https://rohimaya-audiobook-generator.streamlit.app

### Scenario 2: Embedded in Platform (Future)
**Status:** 🔄 Planned  
**Use Case:** Production, unified experience  
**Platform:** Rohimaya Publishing main site

---

## 🏗️ Architecture Options

### Option A: Separate App + Link

**Setup:**
```
Main Platform (Next.js)
    ↓
Link to → Audiobook App (Streamlit)
```

**Pros:**
- ✅ Quick implementation
- ✅ Easy to maintain separately
- ✅ Can deploy independently

**Cons:**
- ❌ Different UI/UX
- ❌ Separate authentication
- ❌ Not seamless experience

---

### Option B: Iframe Embedding

**Setup:**
```
Main Platform (Next.js)
├── /audiobook route
│   └── <iframe src="audiobook-app" />
```

**Code Example:**
```jsx
// pages/audiobook.tsx
export default function AudiobookPage() {
  return (
    <div className="w-full h-screen">
      <iframe
        src="https://rohimaya-audiobook-generator.streamlit.app/?embed=true"
        className="w-full h-full border-0"
        allow="microphone; camera"
      />
    </div>
  );
}
```

**Pros:**
- ✅ Unified navigation
- ✅ Quick integration
- ✅ Keeps Streamlit benefits

**Cons:**
- ❌ Iframe limitations
- ❌ Authentication complexity
- ❌ Styling inconsistencies

---

### Option C: API-Based Integration (Recommended)

**Setup:**
```
Next.js Frontend
    ↓
Cloudflare Worker (API)
    ↓
Prasad's Core Code (Python)
    ↓
TTS Providers
```

**Flow:**
1. User uploads file via Next.js UI
2. Next.js sends to Cloudflare Worker
3. Worker calls Python backend (containers)
4. Python generates audiobook
5. Worker returns audio URL to Next.js
6. User downloads from Next.js

**Pros:**
- ✅ Unified UI/UX
- ✅ Full control
- ✅ Production-ready
- ✅ Scalable

**Cons:**
- ❌ More development time
- ❌ Backend infrastructure needed

---

## 🔐 Authentication Integration

### Current (Standalone)
No authentication - anyone can use

### With Rohimaya Platform

#### Using Supabase Auth

**1. Streamlit App checks session:**
```python
# In streamlit_app.py
import requests

def check_auth():
    # Get token from URL param
    token = st.experimental_get_query_params().get('token', [None])[0]
    
    if not token:
        st.error("Please log in to use this feature")
        st.stop()
    
    # Verify token with Supabase
    response = requests.post(
        "https://your-project.supabase.co/auth/v1/user",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 200:
        st.error("Invalid session")
        st.stop()
    
    return response.json()

# At top of app
user = check_auth()
st.write(f"Welcome, {user['email']}!")
```

**2. Main platform passes token:**
```jsx
// In Next.js
const { session } = useSupabaseAuth();

const audioBookUrl = `https://audiobook.rohimaya.com?token=${session.access_token}`;
```

---

## 💳 Payment Integration

### Usage Tracking

**Add to `streamlit_app.py`:**
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def track_usage(user_id, cost, characters):
    supabase.table('usage').insert({
        'user_id': user_id,
        'feature': 'audiobook',
        'cost': cost,
        'characters': characters,
        'timestamp': datetime.now().isoformat()
    }).execute()

# After generation
track_usage(user['id'], cost_tracker.total_cost, char_count)
```

### Quota Enforcement
```python
def check_quota(user_id, required_chars):
    # Get user's plan
    plan = supabase.table('subscriptions')\
        .select('plan_type')\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    # Get usage this month
    usage = supabase.table('usage')\
        .select('characters')\
        .eq('user_id', user_id)\
        .gte('timestamp', first_day_of_month())\
        .execute()
    
    total_used = sum(u['characters'] for u in usage.data)
    
    # Check limits
    limits = {
        'free': 50000,      # 50K chars
        'basic': 300000,    # 300K chars
        'pro': 1500000      # 1.5M chars
    }
    
    limit = limits.get(plan.data['plan_type'], 0)
    
    if total_used + required_chars > limit:
        return False, f"Quota exceeded. Used: {total_used:,}/{limit:,}"
    
    return True, "OK"

# Before generation
can_generate, message = check_quota(user['id'], len(content))
if not can_generate:
    st.error(message)
    st.stop()
```

---

## 📊 Analytics Integration

### Track Events
```python
import posthog

posthog.api_key = 'your_posthog_key'

# Track generation start
posthog.capture(
    user['id'],
    'audiobook_generation_started',
    properties={
        'word_count': word_count,
        'voice': selected_voice,
        'estimated_cost': est_cost
    }
)

# Track completion
posthog.capture(
    user['id'],
    'audiobook_generation_completed',
    properties={
        'duration': generation_time,
        'cost': actual_cost,
        'file_size': file_size
    }
)
```

---

## 🎨 Branding Consistency

### Match Main Platform

**1. Get CSS from main site:**
```python
# Fetch from main platform
response = requests.get('https://rohimaya.com/api/brand-css')
brand_css = response.text

# Inject into Streamlit
st.markdown(f"<style>{brand_css}</style>", unsafe_allow_html=True)
```

**2. Use shared components:**
```python
# components/rohimaya_header.py
def render_header():
    st.markdown("""
    <div class="rohimaya-header">
        <img src="https://rohimaya.com/logo.png" />
        <h1>Audiobook Generator</h1>
    </div>
    """, unsafe_allow_html=True)
```

---

## 🔄 Data Sync

### User Profile Sync
```python
def sync_user_profile(user_id):
    # Get from main platform
    response = requests.get(
        f'https://api.rohimaya.com/users/{user_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    profile = response.json()
    
    # Store in session
    st.session_state.user_profile = profile
    
    return profile
```

### File Management
```python
def save_to_user_library(user_id, audiobook_path, metadata):
    # Upload to user's Drive folder
    with open(audiobook_path, 'rb') as f:
        files = {'file': f}
        data = {
            'user_id': user_id,
            'title': metadata['title'],
            'voice': metadata['voice'],
            'cost': metadata['cost']
        }
        
        response = requests.post(
            'https://api.rohimaya.com/library/audiobooks',
            files=files,
            data=data,
            headers={'Authorization': f'Bearer {token}'}
        )
    
    return response.json()['url']
```

---

## 🚀 Migration Path

### Phase 1: Standalone (Current)
**Timeline:** Week 1  
**Status:** ✅ Complete
- Separate Streamlit app
- No authentication
- Demo/beta only

### Phase 2: Linked Integration
**Timeline:** Week 2-3  
**Tasks:**
- Add link from main platform
- Implement token-based auth
- Track usage in database
- Enforce quotas

### Phase 3: Iframe Embedding
**Timeline:** Month 2  
**Tasks:**
- Embed in main platform
- Style matching
- Seamless navigation
- Shared session

### Phase 4: Full API Integration
**Timeline:** Month 3-4  
**Tasks:**
- Rebuild UI in Next.js
- Python backend in containers
- Cloudflare Workers API
- Production-ready

---

## 📋 Integration Checklist

### Pre-Integration
- [ ] User authentication working
- [ ] Database schema for usage tracking
- [ ] Stripe integration for payments
- [ ] Quota limits defined
- [ ] Branding guidelines documented

### During Integration
- [ ] API endpoints created
- [ ] Token passing implemented
- [ ] Usage tracking active
- [ ] Error handling robust
- [ ] Testing with real users

### Post-Integration
- [ ] Monitor usage metrics
- [ ] Track error rates
- [ ] Collect user feedback
- [ ] Optimize performance
- [ ] Plan enhancements

---

## 💡 Best Practices

### 1. Start Simple
Begin with standalone app + link, iterate to full integration

### 2. Maintain Separation
Keep audiobook generator as separate module for flexibility

### 3. Test Thoroughly
Test auth, payments, quotas before launch

### 4. Monitor Everything
Track usage, costs, errors, user behavior

### 5. Communicate Status
Show users their quota, costs, generation status

---

## 📞 Integration Support

### For Developers
- API documentation: Coming soon
- Example code: See above
- GitHub issues: For bugs/features

### For Product Team
- User flows: Document in Figma
- Analytics: Set up PostHog events
- Monitoring: Configure alerts

### Contact
- Technical: rohimayapublishing@gmail.com
- Product: [Product lead email]

---

**Integration Guide Version:** 1.0  
**Last Updated:** November 2025  
**Next Review:** After Phase 2 complete
