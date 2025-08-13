'use client';

import React, { useEffect } from 'react';
import type { Metadata } from 'next';
import './globals.css';
import MainLayout from '@/components/layout/main-layout';
import { Toaster } from '@/components/ui/sonner';
import { useFeatureFlagsStore } from '@/stores/feature-flags';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { fetchFlags } = useFeatureFlagsStore();

  useEffect(() => {
    fetchFlags();
  }, [fetchFlags]);

  return (
    <html lang="en">
      <body>
        <MainLayout>{children}</MainLayout>
        <Toaster />
      </body>
    </html>
  );
}