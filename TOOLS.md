# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Sending Media Files (Images, Videos, Documents)

**CRITICAL: When asked to send media files, use the `message` tool directly. DO NOT write Python scripts or use exec.**

### How to Send Media

Use the `message` tool with these parameters:

```json
{
  "action": "send",
  "channel": "whatsapp",
  "target": "120363405179913416@g.us",  // or phone number for DM
  "media": "X:\\full\\path\\to\\file.jpg",
  "caption": "Optional caption text"
}
```

### Common Mistakes to AVOID

❌ **DON'T** write Python scripts to find/catalog/send files
❌ **DON'T** use `exec` tool for file operations
❌ **DON'T** overcomplicate - just use the message tool directly

✅ **DO** use the `message` tool with `media` parameter
✅ **DO** provide full absolute Windows paths (e.g., `X:\data\...`)
✅ **DO** use forward slashes if backslashes cause issues

### Media Locations

- **Photography clients**: `X:\data\lr-clients-x\YYYY-MM-DD ClientName\`
  - Structure: `YYYY-MM-DD ClientName\{proof-70, ps, etc}\filename.jpg`
  - Example: `X:\data\lr-clients-x\2025-11-08 Arunita\proof-70\20251108-3X5A4267.jpg`

### Media Limits

- Max file size: **50MB** (both inbound and outbound)
- Supported formats: JPG, PNG, MP4, PDF, etc.

### Troubleshooting

If media send fails:
1. Verify the file path exists (use `exec` with `dir` command to check)
2. Ensure file size is under 50MB
3. Check that the target is correct (group JID or phone number)
4. Use the message tool directly - don't wrap in scripts

---

## Photo Search Database

**CRITICAL: To find photos, ALWAYS use the `photo-search-all` command.**

This command searches BOTH JPG and RAW databases automatically.

### Database Locations

- **JPG Database**: `x:\openclaw\workspace\photos_full.db` - All exported JPG files
- **RAW Database**: `x:\openclaw\workspace\raw_photos.db` - RAW files with instant-share previews
- **photo-search-all**: Searches BOTH databases in a single command

### How to Search Photos

**When user asks for photos by DATE, use photo-search-all:**

Run this command:
```
photo-search-all --date "2025-02-07" --limit 10
```

This automatically searches:
- Exported JPG files (from lr-clients-x folders)
- RAW file previews (small 100KB JPGs perfect for WhatsApp sharing)

**IMPORTANT:** The command is already installed and ready to use. Just run it directly.

### Search Examples

**Find by client name:**
```bash
photo-search-all "Arunita"
photo-search-all --client "Arunita"
```

**Find by date (searches both JPG and RAW):**
```bash
photo-search-all --date "2025-02-07"
```

**Find by camera:**
```bash
photo-search-all --camera "Canon"
```

**Find photos with GPS location:**
```bash
photo-search-all --location
```

**Combine multiple criteria:**
```bash
photo-search-all --client "Arunita" --date "2025-11-08" --limit 5
```

**Get just the count:**
```bash
photo-search-all --client "Arunita" --count
```

**Get file paths only (simple output):**
```bash
photo-search-all --client "Arunita" --simple
```

### Database Fields Available

- `client_name` - Client name extracted from directory
- `date` - Date in YYYY-MM-DD format
- `camera_make` - Camera manufacturer (e.g., "Sony")
- `camera_model` - Camera model (e.g., "ILCE-7RM5")
- `lens_model` - Lens used
- `iso` - ISO setting
- `aperture` - Aperture (e.g., "f/2.8")
- `shutter_speed` - Shutter speed (e.g., "1/250")
- `focal_length` - Focal length (e.g., "85mm")
- `gps_latitude` - GPS latitude
- `gps_longitude` - GPS longitude
- `folder_type` - Subfolder (e.g., "proof-70", "ps")
- `size_mb` - File size in megabytes

### Common Use Cases

**When user asks "send pics from feb 7" or "photos from february 7":**
Step 1: Search for photos
```
photo-search-all --date "2025-02-07" --limit 10
```
Step 2: Use message tool to send the first result filepath

**When user asks "show me photos from November 8":**
```
photo-search-all --date "2025-11-08" --limit 20
```

**When user asks "find photos taken with Canon camera":**
```
photo-search-all --camera "Canon" --limit 20
```

**When user asks for "previews":**
The RAW previews are automatically included in all photo-search-all results.
They are small (~100KB) JPG files perfect for WhatsApp sharing.

**After finding photos, to send one:**
Use the message tool with the filepath from search results:
```json
{
  "action": "send",
  "channel": "whatsapp",
  "target": "120363405179913416@g.us",
  "media": "X:\\data\\lr-clients-x\\2025-11-08 Arunita\\proof-70\\20251108-3X5A4267.jpg"
}
```

### Important Notes

- ✅ **DO** use `photo-search-all` via exec tool to find photos (searches both JPG and RAW)
- ✅ **DO** use message tool to send found photos
- ✅ **DO** search by date when user mentions dates (e.g., "feb 7" → --date "2025-02-07")
- ❌ **DON'T** try to search filesystem directly
- ❌ **DON'T** write Python scripts to find files
- Both databases are pre-indexed for fast searching
- Results are limited to 50 by default (use --limit to change)
- RAW previews are ~100KB (perfect for WhatsApp sharing)
