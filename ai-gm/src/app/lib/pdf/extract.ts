import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
// @ts-ignore bundler handles ?url imports
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

const globalDoc = typeof globalThis !== 'undefined' ? (globalThis as unknown as { document?: Document }) : undefined;

if (globalDoc?.document) {
  GlobalWorkerOptions.workerSrc = workerSrc;
}

export interface PdfTextPage {
  index: number;
  text: string;
}

export const normalizePdfText = (text: string) =>
  text
    .replace(/\s+/g, ' ')
    .replace(/\s([,.!?:;])/g, '$1')
    .trim();

export const extractTextFromPdf = async (file: File): Promise<PdfTextPage[]> => {
  const data = await file.arrayBuffer();
  const task = getDocument({ data });
  const pdf = await task.promise;
  const pages: PdfTextPage[] = [];

  for (let i = 1; i <= pdf.numPages; i += 1) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .join(' ');
    pages.push({ index: i, text: normalizePdfText(text) });
  }

  return pages;
};

type FileCollection = ArrayLike<File> | Iterable<File>;

export const extractAllText = async (files: FileCollection): Promise<string> => {
  const list = Array.from(files as ArrayLike<File>);
  const pages = await Promise.all(list.map((file) => extractTextFromPdf(file)));
  return pages
    .flat()
    .sort((a, b) => a.index - b.index)
    .map((page) => page.text)
    .join('\n\n');
};
