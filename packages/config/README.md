# Shared Config Package

## Status: 🚧 Placeholder

This package will contain shared configuration constants and types used across both the frontend and backend.

### Planned Contents:
- API endpoint definitions
- Supabase bucket names
- TTS provider constants
- Audio format specifications
- Shared TypeScript/Python types

### Example:
```typescript
// config/buckets.ts
export const BUCKETS = {
  MANUSCRIPTS: 'manuscripts',
  AUDIOBOOKS: 'audiobooks',
} as const;
```

```python
# config/buckets.py
BUCKETS = {
    'MANUSCRIPTS': 'manuscripts',
    'AUDIOBOOKS': 'audiobooks',
}
```

---
**Last Updated:** 2025-11-22
