import React from 'react';
import type { Metadata } from 'next';
import './globals.css';
import MainLayout from '@/components/layout/main-layout';
import { Toaster } from '@/components/ui/sonner';

export const metadata: Metadata = {
  title: 'Crawler Admin',
  description: 'Admin dashboard for the web crawler',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <MainLayout>{children}</MainLayout>
        <Toaster />
      </body>
    </html>
  );
}
