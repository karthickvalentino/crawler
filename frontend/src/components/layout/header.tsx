import React from 'react';
import Link from 'next/link';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { UserNav } from './user-nav';

const Header = () => {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-4 md:px-6">
      <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-lg font-semibold md:text-base"
        >
          <span className="sr-only">Crawler</span>
        </Link>
        <Link
          href="/"
          className="text-foreground transition-colors hover:text-foreground"
        >
          Dashboard
        </Link>
        <Link
          href="/web-pages"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          Web Pages
        </Link>
        <Link
          href="/jobs"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          Jobs
        </Link>
        <Link
          href="/chat"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          Chat
        </Link>
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
            <Link href="/" className="hover:text-foreground">
              Dashboard
            </Link>
            <Link
              href="/web-pages"
              className="text-muted-foreground hover:text-foreground"
            >
              Web Pages
            </Link>
            <Link
              href="/jobs"
              className="text-muted-foreground hover:text-foreground"
            >
              Jobs
            </Link>
            <Link
              href="/chat"
              className="text-muted-foreground hover:text-foreground"
            >
              Chat
            </Link>
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
