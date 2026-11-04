import rss from '@astrojs/rss';
import { getPosts } from '../lib/posts';

export async function GET(context) {
  const posts = await getPosts();
  return rss({
    title: 'Jeremy Lane',
    description: 'Writing by Jeremy Lane.',
    site: context.site,
    items: posts.map(({ id, data }) => ({
      title: data.title,
      description: data.description,
      pubDate: data.date,
      link: `/blog/${id}/`,
    })),
  });
}
