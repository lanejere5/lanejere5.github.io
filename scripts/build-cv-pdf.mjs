// Build public/cv.pdf from src/pages/cv.md, so the PDF and the CV page share one source.
//
// The Markdown is converted to LaTeX using cv/resume.cls (the same class and layout as the
// job-hunt CVs) and compiled with Tectonic. Runs before `astro build`, which then publishes
// the PDF at /cv.pdf.
//
//   node scripts/build-cv-pdf.mjs

import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const root = new URL('../', import.meta.url).pathname;
const SOURCE = `${root}src/pages/cv.md`;
const BUILD = `${root}.cv-build/`;
const OUT = `${root}public/cv.pdf`;

// Links shown under the name. The PDF is public, so no email or phone.
const LINKS = [
  ['https://lanejere5.github.io', 'lanejere5.github.io'],
  ['https://github.com/lanejere5', 'github.com/lanejere5'],
  ['https://www.linkedin.com/in/lanejere5', 'linkedin.com/in/lanejere5'],
  ['https://scholar.google.com/citations?user=atcyxVwAAAAJ', 'Google Scholar'],
];

// ---------- Markdown → LaTeX, inline ----------

const UNICODE = { '–': '--', '—': '---', 'é': "\\'e", '·': '\\textperiodcentered{}', '’': "'" };

function escapeText(s) {
  return s
    .replace(/\\/g, '\\textbackslash{}')
    .replace(/([&%$#_{}])/g, '\\$1')
    .replace(/~/g, '\\textasciitilde{}')
    .replace(/\^/g, '\\textasciicircum{}')
    .replace(/[–—é·’]/g, (c) => UNICODE[c]);
}

function escapeUrl(u) {
  return u.replace(/([%#\\])/g, '\\$1');
}

/** Inline Markdown (links, bold, italics) to LaTeX. */
function inline(md) {
  const links = [];
  let s = md.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, text, url) => {
    links.push([text, url]);
    return `\u0000${links.length - 1}\u0000`;
  });
  s = escapeText(s)
    .replace(/\*\*(.+?)\*\*/g, '\\textbf{$1}')
    .replace(/\*(.+?)\*/g, '\\emph{$1}');
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => {
    const [text, url] = links[i];
    return `\\href{${escapeUrl(url)}}{${inline(text)}}`;
  });
}

const plain = (md) => md.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*+/g, '');

// ---------- Parse cv.md into sections, subsections and items ----------

function parse(md) {
  const body = md.replace(/^---[\s\S]*?---\n/, '');
  const sections = [];
  let section, group, item;
  for (const line of body.split('\n')) {
    let m;
    if ((m = line.match(/^## (.+)/))) {
      section = { title: m[1].trim(), groups: [] };
      sections.push(section);
      group = { title: null, intro: [], items: [] };
      section.groups.push(group);
      item = null;
    } else if ((m = line.match(/^### (.+)/))) {
      group = { title: m[1].trim(), intro: [], items: [] };
      section.groups.push(group);
      item = null;
    } else if ((m = line.match(/^- (.+)/))) {
      item = { head: m[1].trim(), notes: [], details: [], meta: null };
      group.items.push(item);
    } else if ((m = line.match(/^ {4}- (.+)/)) && item) {
      item.details.push(m[1].trim());
    } else if ((m = line.match(/^ {2}<span class="note">(.+)<\/span>/)) && item) {
      item.notes.push(m[1].trim());
    } else if ((m = line.match(/^ {2}\*(.+)\*$/)) && item) {
      item.meta = m[1].trim();
    } else if (line.trim() && !line.startsWith('<') && section) {
      group.intro.push(line.trim());
      item = null;
    }
  }
  return sections;
}

/** Split "…, City *dates*" into [main, dates]. */
function splitDates(head) {
  const m = head.match(/^(.*?)\s+\*([^*]+)\*$/);
  return m ? [m[1], m[2]] : [head, null];
}

/** Split "**Title**, rest" into [title, rest]. */
function splitTitle(head) {
  const m = head.match(/^\*\*(.+?)\*\*,?\s*(.*)$/);
  return m ? [m[1], m[2]] : [head, ''];
}

// ---------- LaTeX per section ----------

const details = (item) =>
  item.details.length
    ? `\\vspace{-\\parskip}\n\\begin{itemize}\n${item.details.map((d) => `  \\item ${inline(d)}`).join('\n')}\n\\end{itemize}\n`
    : '';

/** Experience-style entry: bold title and dates on one line, employer below, then notes and details. */
function position(item) {
  const [head, dates] = splitDates(item.head);
  const [title, rest] = splitTitle(head);
  const lines = [`\\textbf{${inline(title)}} \\hfill ${dates ? inline(dates) : ''}`];
  if (rest) lines.push(inline(rest));
  for (const n of item.notes) lines.push(`{\\smaller ${inline(n)}}`);
  return `${lines.join('\\\\\n')}\n${details(item)}`;
}

/** A year column beside the text, as in the Honors and Talks tables. Breaks across pages. */
function yearTable(rows) {
  const body = rows.map(([year, text]) => `${year} & ${text} \\\\`).join('\n');
  return `\\begin{longtable}{@{}p{2.1cm}p{0.8\\textwidth}@{}}\n${body}\n\\end{longtable}\n`;
}

/** Paper: authors. Title. Venue, year. */
function paper(item) {
  const [authors, venue] = (item.meta ?? '').split(' · ');
  const award = item.head.match(/\s*\(\*\*(.+?)\*\*\)$/);
  const title = item.head.replace(/\s*\(\*\*.+?\*\*\)$/, '');
  return `\\item ${inline(authors ?? '')}. \\emph{${inline(title)}}. ${inline(venue ?? '')}.${award ? ` ${inline(award[1][0].toUpperCase() + award[1].slice(1))}.` : ''}`;
}

function renderSection(section) {
  const name = section.title;
  let out = '';

  if (name === 'Papers') {
    for (const group of section.groups.filter((g) => g.items.length)) {
      out += `\\textbf{${inline(group.title)}}`;
      if (group.intro.length) out += ` {\\smaller (${inline(group.intro.join(' ').replace(/\.$/, ''))})}`;
      out += `\n\\begin{enumerate}[leftmargin=2em, itemsep=2pt, topsep=2pt, label={[\\arabic*]}, resume]\n`;
      out += group.items.map(paper).join('\n');
      out += '\n\\end{enumerate}\n\\vspace{0.3em}\n';
    }
    return out;
  }

  if (name === 'Honors and Awards') {
    const rows = section.groups.flatMap((g) => g.items).map((item) => {
      const m = item.head.match(/^\*\*(.+?)\*\*\s+(.*)$/);
      return [inline(m[1]), inline(m[2])];
    });
    return yearTable(rows);
  }

  if (name === 'Selected Invited Presentations') {
    const rows = section.groups.flatMap((g) =>
      g.items.map((item, i) => {
        const [title, rest] = splitTitle(item.head);
        return [i === 0 ? inline(g.title) : '', `${inline(title)}, ${inline(rest)}`];
      }),
    );
    return `{\\smaller\n${yearTable(rows)}}\n`;
  }

  if (name === 'Teaching') {
    return section.groups
      .filter((g) => g.items.length)
      .map((g) => `\\textbf{${inline(g.title)}}: ${g.items.map((i) => inline(i.head)).join(', ')}.`)
      .join('\\\\\n') + '\n';
  }

  // Experience, Education, Leadership: positions.
  return section.groups
    .flatMap((g) => g.items)
    .map(position)
    .join('\n\\vspace{0.4em}\n');
}

// ---------- Document ----------

function document(sections) {
  const updated = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
  const links = LINKS.map(([url, text]) => `\\href{${escapeUrl(url)}}{${escapeText(text)}}`).join(
    ' \\quad$\\cdot$\\quad\n',
  );
  const body = sections
    .map((s) => `\\begin{workSection}{${escapeText(s.title)}}\n${renderSection(s)}\\end{workSection}\n`)
    .join('\n\\vspace{0.6em}\n');

  return `% Generated by scripts/build-cv-pdf.mjs from src/pages/cv.md. Do not edit.
\\documentclass{resume}

\\usepackage[document]{ragged2e}
\\usepackage{relsize}
\\usepackage{xcolor}
\\usepackage{enumitem}
\\usepackage{longtable}
\\setlength{\\LTpre}{0pt}
\\setlength{\\LTpost}{0pt}
\\setlength{\\LTleft}{0pt}
\\usepackage{fancyhdr}
\\usepackage{lastpage}
\\usepackage{xurl}
\\usepackage{hyperref}
\\hypersetup{colorlinks=true, linkcolor=black, urlcolor=blue}
\\urlstyle{same}

\\setlist[itemize]{leftmargin=1.2em, itemsep=0pt, topsep=0pt, partopsep=0pt, parsep=0pt}

\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{0pt}
\\fancyfoot[L]{\\smaller Jeremy Lane --- Curriculum Vitae}
\\fancyfoot[R]{\\smaller Page \\thepage\\ of \\pageref{LastPage}}
\\geometry{bottom=0.7in, footskip=0.3in}

\\begin{document}
\\thispagestyle{fancy}
\\sloppy

{\\Huge\\bfseries Jeremy Lane}\\\\[0.3em]
\\textsc{Curriculum Vitae} \\hfill Updated ${updated}

\\vspace{0.4em}
${links}

\\vspace{0.8em}

${body}
\\end{document}
`;
}

// ---------- Build ----------

const sections = parse(readFileSync(SOURCE, 'utf8'));
mkdirSync(BUILD, { recursive: true });
copyFileSync(`${root}cv/resume.cls`, `${BUILD}resume.cls`);
writeFileSync(`${BUILD}cv.tex`, document(sections));
execFileSync('tectonic', ['-X', 'compile', 'cv.tex'], { cwd: BUILD, stdio: ['ignore', 'ignore', 'inherit'] });
copyFileSync(`${BUILD}cv.pdf`, OUT);
console.log(`wrote public/cv.pdf (${sections.length} sections from src/pages/cv.md)`);
