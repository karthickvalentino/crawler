"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Globe, Link, Bot, CheckCircle } from "lucide-react";
import RecentCrawls from "@/components/dashboard/recent-crawls";
import { getDashboardAnalytics } from "@/services/api";
import React from "react";

const DashboardPage = () => {
  const [analytics, setAnalytics] = React.useState({
    total_domains: 0,
    total_urls: 0,
    running_crawlers: 0,
    jobs_completed: 0,
  });

  React.useEffect(() => {
    const fetchData = async () => {
      const result = await getDashboardAnalytics();
      setAnalytics(result);
    };
    fetchData();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mt-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Domains
            </CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_domains}</div>
            <p className="text-xs text-muted-foreground">
              Number of unique domains crawled.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total URLs</CardTitle>
            <Link className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_urls}</div>
            <p className="text-xs text-muted-foreground">
              Total number of URLs crawled.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Crawlers Running
            </CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics.running_crawlers}
            </div>
            <p className="text-xs text-muted-foreground">
              Number of active crawlers.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Jobs Completed
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics.jobs_completed}
            </div>
            <p className="text-xs text-muted-foreground">
              Number of crawler jobs completed.
            </p>
          </CardContent>
        </Card>
      </div>
      <RecentCrawls />
    </div>
  );
};

export default DashboardPage;
