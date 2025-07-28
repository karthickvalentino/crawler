"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { startCrawler } from "@/services/api";

interface CreateJobFormProps {
  onJobCreated: () => void;
}

export function CreateJobForm({ onJobCreated }: CreateJobFormProps) {
  const [domain, setDomain] = useState("");
  const [depth, setDepth] = useState(1);
  const [open, setOpen] = useState(false);

  const handleSubmit = async () => {
    try {
      await startCrawler(domain, depth);
      onJobCreated();
      setOpen(false);
    } catch (error) {
      console.error("Failed to start crawler:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Job</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Crawler Job</DialogTitle>
          <DialogDescription>
            Enter the details for the new crawler job.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="domain" className="text-right">
              Domain
            </Label>
            <Input
              id="domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="col-span-3"
              placeholder="example.com"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="depth" className="text-right">
              Depth
            </Label>
            <Input
              id="depth"
              type="number"
              value={depth}
              onChange={(e) => setDepth(parseInt(e.target.value))}
              className="col-span-3"
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleSubmit}>
            Start Crawling
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}