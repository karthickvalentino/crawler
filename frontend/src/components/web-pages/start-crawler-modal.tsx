
"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { startCrawler } from "@/services/api";
import React from "react";
import { toast } from "sonner";

const StartCrawlerModal = () => {
  const [domain, setDomain] = React.useState("");
  const [depth, setDepth] = React.useState(1);
  const [open, setOpen] = React.useState(false);

  const handleSubmit = async () => {
    try {
      await startCrawler(domain, depth);
      setOpen(false);
      toast.success("Crawler job started successfully!");
    } catch (error) {
      console.error(error);
      toast.error("Failed to start crawler job.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Start Crawler</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Start Crawler</DialogTitle>
          <DialogDescription>
            Fill in the details to start a new crawler job.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="domain" className="text-right">
              Domain
            </Label>
            <Input
              id="domain"
              className="col-span-3"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="depth" className="text-right">
              Depth
            </Label>
            <Input
              id="depth"
              type="number"
              className="col-span-3"
              value={depth}
              onChange={(e) => setDepth(parseInt(e.target.value))}
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleSubmit}>
            Start
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default StartCrawlerModal;
