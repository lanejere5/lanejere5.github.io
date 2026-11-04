# lanejere5.github.io

Personal site, built with [Astro](https://astro.build) and deployed to GitHub Pages
from `main`.

| Page | File |
|---|---|
| Home | `src/pages/index.md` (portrait: `src/assets/portrait.png`) |
| CV | `src/pages/cv.md` (also builds the PDF at `/cv.pdf`) |
| Blog posts | `src/content/blog/` |

## Running the site locally

One-time setup (needs Node.js, e.g. `brew install node`):

```bash
npm install
```

Then start the preview server and open http://localhost:4321:

```bash
npm run dev
```

Pages reload automatically as you save. Stop the server with Ctrl+C.

## CV PDF

The downloadable CV (`/cv.pdf`) is generated from `src/pages/cv.md`, so editing that one
file updates both the web page and the PDF. `scripts/build-cv-pdf.mjs` converts the
Markdown to LaTeX using `cv/resume.cls` (the same class as the job-hunt CVs) and compiles
it with [Tectonic](https://tectonic-typesetting.github.io). It runs automatically as the
first step of `npm run build`, locally and on GitHub.

- **Preview the PDF locally:** `npm run cv:pdf`, then open `public/cv.pdf`. (Needs
  Tectonic: `brew install tectonic`.) The PDF is a build output and isn't committed.
- **Keep the CV's Markdown shapes**, since the converter reads them: `##` sections, `###`
  groups, entries as `- **Title**, Employer, … *dates*`, grey lines as
  `<span class="note">…</span>`, and papers as a title line followed by
  `*authors · venue, year*`.
- **Change the PDF's layout:** edit the LaTeX in `scripts/build-cv-pdf.mjs`. The links
  under the name are in its `LINKS` list; the PDF deliberately has no email or phone.

## Adding a blog post (SOP)

### 1. Create the file

Each post is one Markdown file in `src/content/blog/`. The file name becomes the URL:

```
src/content/blog/spinning-solids.md   →   /blog/spinning-solids/
```

Use lowercase words separated by hyphens. If the post has images, use a folder
instead and keep the images beside it:

```
src/content/blog/spinning-solids/
  index.md          →   /blog/spinning-solids/
  rotation.png
```

### 2. Add the front matter

Every post starts with this block. All four fields are checked when the site builds,
and a missing or misspelled one stops the build with an error naming the post.

```markdown
---
title: Why the cube needs only a quarter turn
date: 2026-11-10
description: One sentence for the blog list and link previews.
draft: true
---
```

- `date` is the publication date, `YYYY-MM-DD`. Posts are listed newest first.
- `draft: true` keeps the post off the live site (see step 4).

### 3. Write

Ordinary Markdown, plus:

| Want | Write |
|---|---|
| Section heading | `## Heading` (use `##` and `###`; the title is the page's only top heading) |
| Inline math | `$\omega = dq \wedge dp$` |
| Display math | `$$` on its own line, the equation, then `$$` on its own line |
| Code block | three backticks with a language: <code>```python</code> … <code>```</code> |
| Footnote | `text[^1]` and, anywhere below, `[^1]: The note.` |
| Image | `![Describe the image](./rotation.png)` (folder posts only) |
| Quote | `> Quoted text` |

Math is rendered with KaTeX, so standard LaTeX math commands work. Images are resized
and converted to WebP automatically; always write a real description in the brackets
for screen readers.

You can write posts in Obsidian by opening `src/content/blog/` as a folder. Avoid
Obsidian-only `[[wikilinks]]`; use normal `[text](url)` links.

### 4. Preview the draft

With `npm run dev` running, open http://localhost:4321/blog/. Drafts appear there with
a **Draft** badge. They never appear on the live site, so a draft can be committed
and pushed safely while you work on it.

### 5. Publish

1. Change `draft: true` to `draft: false` and check the `date`.
2. Check it builds: `npm run build` (it should end with `Complete!`).
3. Commit and push to `main`:

   ```bash
   git add src/content/blog
   git commit -m "Add post: Why the cube needs only a quarter turn"
   git push
   ```

4. GitHub Actions rebuilds and deploys the site, usually within a minute. Watch it
   under the repo's **Actions** tab, then open https://lanejere5.github.io/blog/.

The first published post also makes **Blog** appear in the site's page menu and turns on
the RSS feed at https://lanejere5.github.io/rss.xml.

### Editing or removing a post

- **Edit:** change the file and push again.
- **Unpublish:** set `draft: true` and push.
- **Delete:** delete the file (or folder) and push.

## Troubleshooting

- **Build error mentioning a post:** usually a front matter problem: a missing field,
  a date not in `YYYY-MM-DD` form, or `draft` spelled differently.
- **Math shows as raw `$…$`:** check that the dollar signs are paired, and that display
  math has `$$` on lines of their own.
- **Deploy stuck or failed with "Deployment cancelled":** GitHub Pages sometimes stalls.
  Start a fresh run from the **Actions** tab (*Deploy to GitHub Pages* → *Run workflow*),
  or `gh workflow run deploy.yml --ref main`. Re-running the failed run alone can hit the
  same cancelled deployment.

## Other maintenance

- **CV section-break solids and favicon:** generated by `scripts/generate-solids.py`.
  Run `python3 scripts/generate-solids.py` after changing it; it rewrites
  `public/solids/` and `public/favicon.svg`.
- **Colours and typography:** `src/styles/global.css` (light and dark themes are the
  tokens at the top).
