import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Knowledge RAG',
  description: '\u628a\u4f60\u7684\u6536\u85cf\u5939\u53d8\u6210\u53ef\u5bf9\u8bdd\u7684\u77e5\u8bc6\u5e93',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-950 text-gray-100 antialiased">
        <div className="pl-56 min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
