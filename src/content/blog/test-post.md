---
title: A test post
date: 2026-11-03
description: Checking how headings, math, code, quotes, and footnotes look on the blog.
draft: true
---

This is a test post for checking the blog's typography. It is a draft, so it only appears when previewing locally with `npm run dev`, never on the live site.

## Headings and paragraphs

A second-level heading starts each major section. Paragraphs use the same serif type as the rest of the site, with [links like this one](https://lanejere5.github.io/cv/) and occasional *emphasis* or **bold**.

### A smaller heading

Lists work as expected:

- Pre-training on event sequences
- Post-training with verifiable rewards
- Evaluating agents with LLM judges

1. First, define the task.
2. Then, measure it.
3. Finally, improve it.

## Math

Inline math sits in the sentence, like the symplectic form $\omega = \sum_i dq_i \wedge dp_i$ or a Hamiltonian $H\colon M \to \mathbb{R}$. Display math gets its own line:

$$
\{f, g\} = \sum_{i=1}^{n} \left( \frac{\partial f}{\partial q_i} \frac{\partial g}{\partial p_i} - \frac{\partial f}{\partial p_i} \frac{\partial g}{\partial q_i} \right)
$$

## Code

Inline code looks like `torch.compile(model)`. A code block:

```python
def rotate(v, theta):
    """Rotate a 2D vector by theta radians."""
    c, s = math.cos(theta), math.sin(theta)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])
```

## Quotes and footnotes

> Mathematics is the art of giving the same name to different things.

A sentence with a footnote.[^1]

[^1]: Footnotes collect at the end of the post.
