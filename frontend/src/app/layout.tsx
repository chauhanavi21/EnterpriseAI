import type { Metadata } from 'next';
import './globals.css';
import ClientProviders from '@/components/ClientProviders';

export const metadata: Metadata = {
  title: 'Enterprise AI Knowledge Copilot',
  description: 'Production-grade self-hosted AI knowledge management platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
