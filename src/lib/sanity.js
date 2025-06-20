import { createClient } from '@sanity/client';

export const client = createClient({
  projectId: 'j3f6tjvd',
  dataset: 'production',
  apiVersion: '2023-05-03',
  useCdn: true,
});

export function toHtml(portableText) {
  if (!portableText) return '';
  return String(portableText);
}

