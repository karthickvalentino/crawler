'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Chat from '@/components/chat/chat';
import { useFeatureFlagsStore } from '@/stores/feature-flags';

export default function ChatPage() {
  const { flags, isLoaded } = useFeatureFlagsStore();
  const router = useRouter();

  useEffect(() => {
    // If flags are loaded and the chat_ui flag is not enabled, redirect to the homepage.
    if (isLoaded && !flags.chat_ui) {
      router.replace('/');
    }
  }, [isLoaded, flags, router]);

  // If flags are not loaded yet, or if the feature is disabled, show a loading state or null.
  // This prevents a flash of the chat UI before the redirect can happen.
  if (!isLoaded || !flags.chat_ui) {
    return null; // Or a loading spinner
  }

  return (
    <div className="h-full">
      <Chat />
    </div>
  );
}