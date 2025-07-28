
"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import React from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import { getJobs, stopCrawler, deleteJob } from "@/services/api";
import { CreateJobForm } from "./CreateJobForm";

export interface Job {
  id: string;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed" | "stopped" | "queued" | "stopping";
  parameters: {
    domain: string;
    depth: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
  result?: any;
}

const columns: ColumnDef<Job>[] = [
  {
    accessorKey: "id",
    header: "Job ID",
  },
  {
    accessorKey: "parameters.domain",
    header: "Domain",
  },
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "job_type",
    header: "Type",
  },
  {
    accessorKey: "created_at",
    header: "Created At",
  },
  {
    accessorKey: "updated_at",
    header: "Updated At",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const job = row.original;

      const handleStop = async () => {
        try {
          await stopCrawler(job.id);
        } catch (error) {
          console.error("Failed to stop job:", error);
        }
      };

      const handleDelete = async () => {
        try {
          await deleteJob(job.id);
        } catch (error) {
          console.error("Failed to delete job:", error);
        }
      };

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(job.id)}
            >
              Copy job ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>View details</DropdownMenuItem>
            <DropdownMenuItem onClick={handleStop}>Stop job</DropdownMenuItem>
            <DropdownMenuItem
              onClick={handleDelete}
              className="text-red-500"
            >
              Delete job
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

const Jobs = () => {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [data, setData] = React.useState<Job[]>([]);

  const fetchData = async () => {
    const result = await getJobs();
    setData(result);
  };

  React.useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting,
    },
  });

  return (
    <div>
      <div className="flex justify-end mb-4">
        <CreateJobForm onJobCreated={fetchData} />
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className="even:bg-muted"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default Jobs;
