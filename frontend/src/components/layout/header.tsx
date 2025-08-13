'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { UserNav } from './user-nav';
import { useFeatureFlagsStore } from '@/stores/feature-flags';
import clsx from 'clsx';

const Header = () => {
  const { flags, isLoaded } = useFeatureFlagsStore();
  const pathname = usePathname();

  const navLinks = [
    { href: '/', text: 'Dashboard' },
    { href: '/web-pages', text: 'Web Pages' },
    { href: '/jobs', text: 'Jobs' },
    { href: '/chat', text: 'Chat', featureFlag: 'chat_ui' },
  ];

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-4 md:px-6">
      <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-lg font-semibold md:text-base"
        >
          <span className="sr-only">Crawler</span>
        </Link>
        {navLinks.map((link) => {
          if (link.featureFlag && (!isLoaded || !flags[link.featureFlag])) {
            return null;
          }
          return (
            <Link
              key={link.href}
              href={link.href}
              className={clsx(
                'transition-colors hover:text-foreground',
                pathname === link.href
                  ? 'text-foreground'
                  : 'text-muted-foreground'
              )}
            >
              {link.text}
            </Link>
          );
        })}
      </nav>
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" size="icon" className="shrink-0 md:hidden">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle navigation menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left">
          <nav className="grid gap-6 text-lg font-medium">
            <Link
              href="/"
              className="flex items-center gap-2 text-lg font-semibold"
            >
              <span className="sr-only">Crawler</span>
            </Link>
            {navLinks.map((link) => {
              if (link.featureFlag && (!isLoaded || !flags[link.featureFlag])) {
                return null;
              }
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={clsx(
                    'hover:text-foreground',
                    pathname === link.href
                      ? 'text-foreground'
                      : 'text-muted-foreground'
                  )}
                >
                  {link.text}
                </Link>
              );
            })}
          </nav>
        </SheetContent>
      </Sheet>
      <div className="flex items-center gap-4">
        <UserNav />
      </div>
    </header>
  );
};

export default Header;
