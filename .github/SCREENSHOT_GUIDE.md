# Screenshot Guide for README.md

This guide tells you exactly what screenshots to take and where to save them.

## 📁 Location

Save all screenshots in: `.github/screenshots/`

## 📸 Screenshots Needed (Just 3!)

### 1. `hero-banner.png` (OPTIONAL - for top of README)
**What to capture:** Eye-catching banner/hero image
- Full application view showing both input and output panels in action
- Display example questions in the left panel
- Show generated answers in the right panel with sources
- Make it look polished and professional
- **Recommended size:** 1200x600px (wide banner format)

**Tips:**
- This is optional but makes a great first impression
- Use a clean, complete example with good data
- Make sure the interface looks balanced

---

### 2. `main-interface.png` ⭐ REQUIRED
**What to capture:** The full application interface showing the workflow
- Left panel: Input with grant questions and optional context
- Right panel: Generated results with answers
- Show at least 1-2 complete answer cards with sources visible
- Include the header and all main UI elements
- **Recommended size:** 1400x900px (full app view)

**Tips:**
- This is THE main screenshot - make it count!
- Show a real example in action (after clicking "Generate Draft")
- Make sure answers and sources are clearly visible
- Demonstrate the split-pane design and workflow

---

### 3. `results-with-sources.png` ⭐ REQUIRED
**What to capture:** Close-up of generated answers with source citations
- Show 1-2 complete answer cards
- **Emphasize the "Sources" section** at the bottom showing citations
- Show the copy button on each card
- Make sources clearly readable (e.g., "Quantitative → PHC Impact 2024")
- **Recommended size:** 1000x800px

**Tips:**
- This demonstrates the key feature: source attribution
- Pick answers with good, varied sources
- Make sure source citations are front and center
- Show that answers are comprehensive and well-formatted

---

### 4. `sponsor-fit-analysis.png` ⭐ REQUIRED
**What to capture:** The sponsor tailoring section (appears when you provide sponsor context)
- "How We Tailored Your Responses" section
- **Fit Score** prominently displayed (e.g., "4.5/5.0")
- "Fit Analysis" explanation text
- Show this appears AFTER/BELOW the regular answer cards
- **Recommended size:** 1000x700px

**Tips:**
- Generate answers WITH sponsor context to see this section
- Example context: "This grant is from Kaiser Permanente, focusing on health equity and community health programs"
- Make sure the fit score number is very visible
- Show the detailed, honest fit explanation

---

## 🎨 Screenshot Tips

### General Guidelines
1. **Clean interface** - Hide unnecessary browser toolbars
2. **Use compelling examples** - Pick well-written responses with good data
3. **No personal info** - Don't include real API keys or sensitive data
4. **High resolution** - Use at least 1920x1080 screen resolution
5. **Readable text** - Use browser zoom if needed (Cmd/Ctrl + +/-)

### Recommended Tools
- **macOS:** Cmd + Shift + 4 (select area)
- **Windows:** Windows + Shift + S (Snipping Tool)
- **Chrome DevTools:** F12 → Cmd/Ctrl + Shift + P → "Capture screenshot"

### For Best Results
- Use a real example (e.g., "What is your organization's mission?" or Kaiser Permanente grant)
- Make sure source citations are clearly visible
- Capture the full workflow in screenshot #2
- For sponsor fit analysis, actually provide sponsor context when generating

---

## ✅ Quick Checklist

After taking screenshots, verify:

- [ ] At minimum 3 required screenshots are saved in `.github/screenshots/`
- [ ] Files are named exactly as specified (lowercase, with hyphens)
- [ ] All screenshots are PNG format
- [ ] Text is readable and clear
- [ ] No sensitive information visible (API keys, etc.)
- [ ] Images look professional and polished
- [ ] File sizes are reasonable (< 2MB each)

---

## 🚀 Quick Example Workflow for Screenshots

1. **Start the app:**
   ```bash
   ./run_local.sh
   # Open http://localhost:8080
   ```

2. **For screenshot #2 (main interface):**
   - Paste example questions in left panel
   - Click "Generate Draft"
   - Wait for results
   - Take full-screen screenshot

3. **For screenshot #3 (results with sources):**
   - Scroll to show answer cards
   - Make sure "Sources:" section is visible
   - Zoom in if needed, take screenshot

4. **For screenshot #4 (sponsor fit):**
   - Click "Clear All"
   - Paste questions + sponsor context in the context box
   - Generate again
   - Scroll to bottom where fit analysis appears
   - Take screenshot of that section

## 🔄 If You Need to Retake

Just replace the file with the same name. The README will automatically use the updated image.

---

That's it! Just 3-4 screenshots and you're done. 🎉

