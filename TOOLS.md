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
