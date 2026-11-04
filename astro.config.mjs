// @ts-check
import { defineConfig } from 'astro/config';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: 'https://lanejere5.github.io',
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
    // Code blocks follow the site's light/dark theme (see global.css).
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark' },
    },
  },
});
