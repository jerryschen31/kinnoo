# Task306 Smoke Tests - Landing/Header Visual Polish (v2)

## Goal
Validate landing-page and header polish updates introduced by task306.

## Automated checks

### 1) Header brand link and menu links
```bash
grep -n "href=\"/\"" web/components/blocks/MainLayout.tsx
grep -n "kinnoo" web/components/blocks/MainLayout.tsx
grep -n "github.com/jerryschen31/kinnoo" web/components/blocks/MainLayout.tsx
grep -n "github.com/jerryschen31/kinnoo/tree/master/docs" web/components/blocks/MainLayout.tsx
grep -n "github.com/jerryschen31/kinnoo/issues" web/components/blocks/MainLayout.tsx
```
Pass if all five checks find matches.

### 2) Hero text hierarchy and color classes
```bash
grep -n "text-kinnoo-accent" "web/app/(public)/page.tsx"
grep -n "kinnoo" "web/app/(public)/page.tsx"
grep -n "Package, publish, share your AI agents with the world" "web/app/(public)/page.tsx"
grep -n "Take any AI agent" "web/app/(public)/page.tsx"
grep -n "text-5xl\|sm:text-6xl" "web/app/(public)/page.tsx"
grep -n "text-base\|sm:text-lg" "web/app/(public)/page.tsx"
```
Pass if all checks find matches and the large heading text is `kinnoo`.

### 3) Terminal and feature card styling hooks
```bash
grep -n "border-2" web/components/blocks/TerminalPreview.tsx
grep -n "bg-\[#222222\]" web/components/blocks/TerminalPreview.tsx
grep -n "hover:border-\[#3B82F6\]" web/components/blocks/TerminalPreview.tsx
grep -n "border-2" web/components/blocks/FeatureGrid.tsx
grep -n "bg-\[#222222\]" web/components/blocks/FeatureGrid.tsx
grep -n "hover:border-\[#3B82F6\]" web/components/blocks/FeatureGrid.tsx
```
Pass if all checks find matches.

### 4) Header kinnoo size + button hover hooks
```bash
grep -n "text-lg\|sm:text-xl" web/components/blocks/MainLayout.tsx
grep -n "hover:border-\[#3B82F6\]" web/components/blocks/MainLayout.tsx
grep -n "bg-\[#222222\]" web/components/blocks/MainLayout.tsx
grep -n "aria-label=\"Open menu\"" web/components/blocks/MainLayout.tsx
grep -n "left: \"max(1rem, calc((100vw - 72rem) / 2 + 1rem))\"" web/components/blocks/MainLayout.tsx
```
Pass if all checks find matches and the Open menu button does not include a blue hover-border class.

### 5) Feature section heading style
```bash
grep -n "Why builders choose kinnoo" "web/app/(public)/page.tsx"
grep -n "uppercase" "web/app/(public)/page.tsx"
```
Pass if heading exists and class list includes uppercase styling.

### 6) Build smoke
```bash
cd web && npm run build
```
Pass if build exits 0.

## Manual visual checks

1. Run dev server:
```bash
cd web && npm run dev
```
2. Open http://localhost:3000/ and verify:
- `kinnoo` text appears next to hamburger and is clickable back to `/`.
- Header `kinnoo` next to hamburger appears larger than before.
- Hero shows slightly smaller blue `kinnoo`, then larger uppercase slogan line, then long descriptive paragraph.
- Terminal box has thicker border, dark gray background (#222222), and blue border on hover.
- `Why builders choose kinnoo` appears smaller and uppercase.
- All six feature cards have thicker border, dark gray background (#222222), and blue border on hover.
3. Click hamburger and verify sheet background is solid dark gray (#222222), opens aligned with the shared content column (not viewport edge), and links open:
- https://github.com/jerryschen31/kinnoo
- https://github.com/jerryschen31/kinnoo/tree/master/docs
- https://github.com/jerryschen31/kinnoo/issues
4. Verify Login and Sign Up buttons show blue border (#3B82F6) on hover.
5. Verify hamburger button hover remains neutral (no blue highlight).

Pass if all visual checks match expected behavior.
