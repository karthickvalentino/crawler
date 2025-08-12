'use client';

import React, { useState } from 'react';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport, TextStreamChatTransport } from 'ai';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export default function Chat() {
  const { messages, sendMessage, status } = useChat({
    // The API endpoint that proxies to the backend.
    transport: new TextStreamChatTransport({
      api: '/api/chat',
    }),
    onFinish: (message) => {
      console.log('Finished streaming message:', message);
    },
    onError: (error) => {
      // TODO: Handle errors appropriately in your application.
      console.error('An error occurred:', error);
    },
    onData: (data) => {
      console.log('Received data part from server:', data);
    },
  });

  // The input state is managed locally.
  const [input, setInput] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim()) return;

    // The `sendMessage` function sends the user's message to the backend.
    sendMessage({
      parts: [{ type: 'text', text: input }],
    });

    // Clear the input field after sending.
    setInput('');
  };
  const isLoading = false;

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Chat with your crawled data</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col">
        <ScrollArea className="flex-grow mb-4 pr-4">
          {messages.map((m) => (
            <div key={m.id} className="flex items-start gap-4 mb-4">
              <Avatar>
                <AvatarFallback>
                  {m.role === 'user' ? 'U' : 'AI'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-grow">
                <p className="font-bold">
                  {m.role === 'user' ? 'You' : 'Assistant'}
                </p>
                {m.parts.map((part) => {
                  if (part.type === 'text') {
                    return <div key={`${m.id}-text`}>{part.text}</div>;
                  }
                })}
              </div>
            </div>
          ))}
        </ScrollArea>
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder="Ask a question..."
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
