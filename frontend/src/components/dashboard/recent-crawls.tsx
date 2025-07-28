
"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getWebPages } from "@/services/api";
import React from "react";
import { WebPage } from "../web-pages/web-pages";

const RecentCrawls = () => {
  const [recentCrawls, setRecentCrawls] = React.useState<WebPage[]>([]);

  React.useEffect(() => {
    const fetchData = async () => {
      const result = await getWebPages(5, 0, "last_crawled", "desc", "");
      setRecentCrawls(result.data);
    };
    fetchData();
  }, []);

  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold mb-4">Recent Crawls</h2>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Domain</TableHead>
              <TableHead>URL</TableHead>
              <TableHead>Crawled At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentCrawls.map((crawl, index) => (
              <TableRow key={index}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8">
                      <AvatarImage
                        src={`https://logo.clearbit.com/${crawl.domain}`}
                        alt={crawl.domain}
                      />
                      <AvatarFallback>
                        {crawl.domain.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    {crawl.domain}
                  </div>
                </TableCell>
                <TableCell>{crawl.url}</TableCell>
                <TableCell>{new Date(crawl.last_crawled).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default RecentCrawls;
