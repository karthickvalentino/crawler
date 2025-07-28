
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { FileText, Briefcase } from "lucide-react";

const Sidebar = () => {
  const pathname = usePathname();

  const getSidebarLinks = () => {
    if (pathname.startsWith("/web-pages")) {
      return (
        <Link
          href="/web-pages"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
        >
          <FileText className="h-4 w-4" />
          Web Pages
        </Link>
      );
    }
    if (pathname.startsWith("/jobs")) {
      return (
        <Link
          href="/jobs"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
        >
          <Briefcase className="h-4 w-4" />
          Jobs
        </Link>
      );
    }
    return null;
  };

  return (
    <aside className="hidden border-r bg-muted/40 md:block">
      <div className="flex h-full max-h-screen flex-col gap-2">
        <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Image
              src="/logo.png"
              alt="Spider Logo"
              width={40}
              height={40}
              className="h-10 w-10 mix-blend-multiply"
            />
            <span className="">Crawler</span>
          </Link>
        </div>
        <div className="flex-1">
          <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
            {getSidebarLinks()}
          </nav>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
