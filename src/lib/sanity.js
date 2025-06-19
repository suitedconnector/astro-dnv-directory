// src/lib/sanity.js
import { createClient } from '@sanity/client';

export const client = createClient({
  projectId: import.meta.env.SANITY_PROJECT_ID, // Get this from manage.sanity.io
  dataset: import.meta.env.SANITY_DATASET,     // Usually 'production'
  apiVersion: '2023-03-01', // Use a fixed API version
  useCdn: true, // `false` if you want to ensure fresh data
});

// For converting Portable Text (rich text from Sanity) to HTML
import { toHTML } from '@portabletext/to-html';

export function toHtml(portableText) {
  return toHTML(portableText);
}

